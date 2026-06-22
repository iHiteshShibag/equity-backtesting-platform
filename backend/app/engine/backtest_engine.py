import yfinance as yf
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Literal, Optional
from datetime import date, timedelta

from app.engine.filters import apply_filters
from app.engine.rankers import rank_stocks
from app.engine.sizers import compute_weights
from app.engine.metrics import compute_metrics


@dataclass
class BacktestConfig:
    start_date: date
    end_date: date
    initial_capital: float = 1_000_000
    portfolio_size: int = 20
    rebalance_freq: str = "quarterly"
    position_sizing: str = "equal"
    sizing_metric: Optional[str] = None
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    roce_min: Optional[float] = None
    pat_positive: bool = True
    rank_metrics: list = field(default_factory=list)


class BacktestEngine:
    def __init__(self, config: BacktestConfig, db):
        self.cfg = config
        self.db = db

    def run(self) -> dict:
        rebalance_dates = self._get_rebalance_dates()
        if not rebalance_dates:
            return {"error": "No rebalance dates found in range"}

        capital = self.cfg.initial_capital
        portfolio = {}
        timeseries = []
        rebalance_logs = []
        stock_returns = {}

        all_price_data = self._load_all_prices()
        all_fund_data = self._load_all_fundamentals()

        if all_price_data.empty:
            return {"error": "No price data found. Please run data ingestion first."}

        trading_dates = sorted(all_price_data["date"].unique())
        trading_dates = [d for d in trading_dates
                         if self.cfg.start_date <= d <= self.cfg.end_date]

        for i, rb_date in enumerate(rebalance_dates):
            next_rb = rebalance_dates[i + 1] if i + 1 < len(rebalance_dates) else self.cfg.end_date

            # Liquidate existing holdings at rb_date close
            if portfolio:
                prices_on_date = self._get_prices_on(all_price_data, rb_date)
                new_capital = 0
                for ticker, pos in portfolio.items():
                    price = prices_on_date.get(ticker, pos["buy_price"])
                    pnl = (price - pos["buy_price"]) / pos["buy_price"]
                    stock_returns[ticker] = stock_returns.get(ticker, [])
                    stock_returns[ticker].append(pnl)
                    new_capital += pos["shares"] * price
                capital = new_capital

            # Select universe with fundamentals available BEFORE rb_date (no look-ahead)
            universe = all_fund_data[all_fund_data["report_date"] < rb_date].copy()
            if universe.empty:
                universe = all_fund_data.copy()  # fallback for early dates

            # Keep only latest fundamental per stock
            universe = universe.sort_values("report_date").groupby("ticker").last().reset_index()

            # Apply filters
            filtered = apply_filters(universe, self.cfg)

            if filtered.empty:
                timeseries.append({"date": str(rb_date), "portfolio_value": capital, "drawdown": 0})
                continue

            # Rank and select top N
            ranked = rank_stocks(filtered, self.cfg.rank_metrics)
            selected = ranked.head(self.cfg.portfolio_size)

            # Compute weights
            weights = compute_weights(selected, self.cfg)

            # Buy at next available trading day open
            buy_prices = self._get_prices_on(all_price_data, rb_date)

            portfolio = {}
            for _, row in selected.iterrows():
                ticker = row["ticker"]
                w = weights.get(ticker, 0)
                price = buy_prices.get(ticker)
                if price and price > 0 and w > 0:
                    alloc = capital * w
                    shares = alloc / price
                    portfolio[ticker] = {
                        "shares": shares,
                        "buy_price": price,
                        "weight": round(w, 4),
                        "ticker": ticker,
                        "name": row.get("name", ticker),
                    }

            # Track daily portfolio value in this period
            period_dates = [d for d in trading_dates if rb_date <= d < next_rb]
            period_values = []
            for d in period_dates:
                prices = self._get_prices_on(all_price_data, d)
                value = sum(
                    pos["shares"] * prices.get(t, pos["buy_price"])
                    for t, pos in portfolio.items()
                )
                period_values.append(value)
                timeseries.append({"date": str(d), "portfolio_value": round(value, 2)})

            rebalance_logs.append({
                "date": str(rb_date),
                "portfolio_value": round(capital, 2),
                "num_stocks": len(portfolio),
                "holdings": [
                    {
                        "ticker": t,
                        "name": v["name"],
                        "weight": f"{v['weight']*100:.1f}%",
                        "buy_price": round(v["buy_price"], 2),
                    }
                    for t, v in portfolio.items()
                ],
            })

        # Final liquidation
        if portfolio and trading_dates:
            last_prices = self._get_prices_on(all_price_data, trading_dates[-1])
            final_value = sum(
                pos["shares"] * last_prices.get(t, pos["buy_price"])
                for t, pos in portfolio.items()
            )
        else:
            final_value = capital

        # Build timeseries dataframe for metrics
        ts_df = pd.DataFrame(timeseries)
        if ts_df.empty:
            return {"error": "Backtest produced no data"}

        ts_df["date"] = pd.to_datetime(ts_df["date"])
        ts_df = ts_df.sort_values("date").drop_duplicates("date").set_index("date")

        # Compute drawdown
        rolling_max = ts_df["portfolio_value"].cummax()
        ts_df["drawdown"] = ((ts_df["portfolio_value"] - rolling_max) / rolling_max * 100).round(2)

        metrics = compute_metrics(ts_df["portfolio_value"], self.cfg.initial_capital)

        benchmark_metrics = self._get_benchmark_metrics()

        result_ts = ts_df.reset_index()

        result_ts["date"] = result_ts["date"].dt.strftime("%Y-%m-%d")
        result_ts["portfolio_value"] = result_ts["portfolio_value"].round(2)

        # Winners and losers
        flat_returns = {
            t: round(np.mean(rets) * 100, 2)
            for t, rets in stock_returns.items()
        }
        sorted_returns = sorted(flat_returns.items(), key=lambda x: x[1], reverse=True)
        winners = [{"ticker": t, "return_pct": r} for t, r in sorted_returns[:5]]
        losers  = [{"ticker": t, "return_pct": r} for t, r in sorted_returns[-5:]]

        return {
            "timeseries": result_ts.to_dict("records"),
            "rebalance_logs": rebalance_logs,
            "metrics": metrics,
            "benchmark": benchmark_metrics,
            "winners": winners,
            "losers": losers,
        }

    def _get_rebalance_dates(self):
        freq_map = {"monthly": "MS", "quarterly": "QS", "yearly": "YS"}
        freq = freq_map.get(self.cfg.rebalance_freq, "QS")
        dates = pd.date_range(self.cfg.start_date, self.cfg.end_date, freq=freq)
        return [d.date() for d in dates]

    def _load_all_prices(self) -> pd.DataFrame:
        from sqlalchemy import text
        sql = text("""
            SELECT s.ticker, p.date, p.open, p.close,
                   COALESCE(p.adj_close, p.close) as adj_close
            FROM daily_prices p
            JOIN stocks s ON s.id = p.stock_id
            WHERE p.date BETWEEN :start AND :end
            ORDER BY p.date
        """)
        try:
            return pd.read_sql(sql, self.db.bind,
                               params={"start": self.cfg.start_date, "end": self.cfg.end_date})
        except Exception:
            return pd.DataFrame()

    def _load_all_fundamentals(self) -> pd.DataFrame:
        from sqlalchemy import text
        sql = text("""
            SELECT s.ticker, s.name, s.sector,
                   f.report_date, f.market_cap, f.roce, f.roe,
                   f.pe_ratio, f.pb_ratio, f.pat, f.capital_employed,
                   f.total_debt, f.total_equity
            FROM fundamentals f
            JOIN stocks s ON s.id = f.stock_id
            WHERE f.period_type = 'annual'
            ORDER BY f.report_date
        """)
        try:
            return pd.read_sql(sql, self.db.bind)
        except Exception:
            return pd.DataFrame()
        
    def _get_benchmark_metrics(self):
        try:
            nifty = yf.download(
                "^NSEI",
                start=str(self.cfg.start_date),
                end=str(self.cfg.end_date),
                progress=False,
                auto_adjust=True
            )

            if nifty.empty:
                return None

            values = nifty["Close"].squeeze()

            if values.empty:
                return None

            initial_value = float(values.iloc[0])

            from app.engine.metrics import compute_metrics

            return compute_metrics(
                values,
                initial_value
            )

        except Exception as e:
            print("Benchmark error:", e)
            return None

    def _get_prices_on(self, price_df: pd.DataFrame, target_date: date) -> dict:
        # Get most recent price on or before target_date
        sub = price_df[price_df["date"] <= target_date]
        if sub.empty:
            return {}
        latest = sub.sort_values("date").groupby("ticker").last()
        return latest["adj_close"].to_dict()
