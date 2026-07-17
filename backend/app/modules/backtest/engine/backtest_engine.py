import logging

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional
from datetime import date

from app.modules.backtest.engine.filters import apply_filters
from app.modules.backtest.engine.rankers import rank_stocks
from app.modules.backtest.engine.sizers import compute_weights
from app.modules.backtest.engine.metrics import compute_metrics
from app.modules.market_data.index_membership import get_active_tickers

logger = logging.getLogger(__name__)


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
    commission_bps: float = 0
    slippage_pct: float = 0

    @classmethod
    def from_request_dict(cls, req: dict) -> "BacktestConfig":
        """Build a config from a BacktestRequest.model_dump(mode='json') dict
        (as stored on BacktestJob.request / SavedStrategy.request). Shared by
        both the one-off backtest task and the saved-strategy rebalance task
        so the request -> config mapping only lives in one place."""
        from app.modules.backtest.schemas import RankMetric

        return cls(
            start_date=date.fromisoformat(req["start_date"]),
            end_date=date.fromisoformat(req["end_date"]),
            initial_capital=req["initial_capital"],
            portfolio_size=req["portfolio_size"],
            rebalance_freq=req["rebalance_freq"],
            position_sizing=req["position_sizing"],
            sizing_metric=req.get("sizing_metric"),
            market_cap_min=req.get("market_cap_min"),
            market_cap_max=req.get("market_cap_max"),
            roce_min=req.get("roce_min"),
            pat_positive=req["pat_positive"],
            rank_metrics=[RankMetric(**rm) for rm in req.get("rank_metrics", [])],
            commission_bps=req["commission_bps"],
            slippage_pct=req["slippage_pct"],
        )


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
        trade_returns = []
        total_costs = 0.0
        periods_without_pit_data = 0
        commission_rate = self.cfg.commission_bps / 10000
        slippage_rate = self.cfg.slippage_pct / 100

        all_price_data = self._load_all_prices()
        all_fund_data = self._load_all_fundamentals()

        if all_price_data.empty:
            return {"error": "No price data found. Please run data ingestion first."}

        trading_dates = sorted(all_price_data["date"].unique())
        trading_dates = [d for d in trading_dates
                         if self.cfg.start_date <= d <= self.cfg.end_date]

        # Pivot once into a date-indexed, forward-filled ticker matrix so each
        # _get_prices_on() call below is an index search instead of re-filtering
        # and re-grouping the entire price history on every single trading day.
        price_matrix = self._build_price_matrix(all_price_data)

        for i, rb_date in enumerate(rebalance_dates):
            next_rb = rebalance_dates[i + 1] if i + 1 < len(rebalance_dates) else self.cfg.end_date

            # Liquidate existing holdings at rb_date close
            if portfolio:
                prices_on_date = self._get_prices_on(price_matrix, rb_date)
                new_capital = 0
                for ticker, pos in portfolio.items():
                    raw_price = prices_on_date.get(ticker, pos["buy_price"])
                    sell_price = raw_price * (1 - slippage_rate)
                    gross_proceeds = pos["shares"] * sell_price
                    commission = gross_proceeds * commission_rate
                    net_proceeds = gross_proceeds - commission
                    total_costs += commission

                    pnl = (net_proceeds - pos["invested"]) / pos["invested"] if pos["invested"] else 0
                    stock_returns[ticker] = stock_returns.get(ticker, [])
                    stock_returns[ticker].append(pnl)
                    trade_returns.append(pnl)
                    new_capital += net_proceeds
                capital = new_capital
                # Holdings are now fully cashed out into `capital` -- clear the dict so a
                # period skipped below (no point-in-time data / nothing passes filters)
                # doesn't re-liquidate these same stale positions again next iteration.
                portfolio = {}

            # Select universe with fundamentals available BEFORE rb_date (no look-ahead).
            # If nothing qualifies, we have no genuine point-in-time fundamentals for this
            # rebalance -- fundamentals.py stamps report_date at ingestion time, not the
            # actual fiscal period, so there may simply be no record older than rb_date.
            # Skip the period (hold cash) rather than silently reusing today's fundamentals
            # for a historical date, which would invalidate the whole backtest.
            universe = all_fund_data[all_fund_data["report_date"] < rb_date].copy()
            if universe.empty:
                periods_without_pit_data += 1
                timeseries.append({"date": str(rb_date), "portfolio_value": capital, "drawdown": 0})
                rebalance_logs.append({
                    "date": str(rb_date),
                    "portfolio_value": round(capital, 2),
                    "num_stocks": 0,
                    "holdings": [],
                    "data_status": "skipped_no_point_in_time_fundamentals",
                })
                continue

            # Keep only latest fundamental per stock
            universe = universe.sort_values("report_date").groupby("ticker").last().reset_index()

            # Restrict to tickers that were actually NIFTY100 members on rb_date
            # (point-in-time membership) -- without this, every ticker ever
            # ingested is eligible at every historical date regardless of
            # whether it was in the index then, which is a survivorship-bias
            # bug (e.g. a 2021-IPO stock appearing "selectable" in 2016).
            active_tickers = get_active_tickers(self.db, "NIFTY100", rb_date)
            if active_tickers:
                universe = universe[universe["ticker"].isin(active_tickers)]

            # Apply filters
            filtered = apply_filters(universe, self.cfg)

            if filtered.empty:
                timeseries.append({"date": str(rb_date), "portfolio_value": capital, "drawdown": 0})
                rebalance_logs.append({
                    "date": str(rb_date),
                    "portfolio_value": round(capital, 2),
                    "num_stocks": 0,
                    "holdings": [],
                    "data_status": "skipped_no_stocks_passed_filters",
                })
                continue

            # Rank and select top N
            ranked = rank_stocks(filtered, self.cfg.rank_metrics)
            selected = ranked.head(self.cfg.portfolio_size)

            # Compute weights
            weights = compute_weights(selected, self.cfg)

            # Buy at next available trading day open
            buy_prices = self._get_prices_on(price_matrix, rb_date)

            portfolio = {}
            for _, row in selected.iterrows():
                ticker = row["ticker"]
                w = weights.get(ticker, 0)
                price = buy_prices.get(ticker)
                if price and price > 0 and w > 0:
                    alloc = capital * w
                    buy_price = price * (1 + slippage_rate)
                    commission = alloc * commission_rate
                    total_costs += commission
                    net_alloc = alloc - commission
                    shares = net_alloc / buy_price
                    portfolio[ticker] = {
                        "shares": shares,
                        "buy_price": buy_price,
                        "invested": net_alloc,
                        "weight": round(w, 4),
                        "ticker": ticker,
                        "name": row.get("name", ticker),
                    }

            # Track daily portfolio value in this period
            period_dates = [d for d in trading_dates if rb_date <= d < next_rb]
            period_values = []
            for d in period_dates:
                prices = self._get_prices_on(price_matrix, d)
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
                "data_status": "ok",
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
            last_prices = self._get_prices_on(price_matrix, trading_dates[-1])
            final_value = 0
            for t, pos in portfolio.items():
                raw_price = last_prices.get(t, pos["buy_price"])
                sell_price = raw_price * (1 - slippage_rate)
                gross_proceeds = pos["shares"] * sell_price
                commission = gross_proceeds * commission_rate
                net_proceeds = gross_proceeds - commission
                total_costs += commission
                pnl = (net_proceeds - pos["invested"]) / pos["invested"] if pos["invested"] else 0
                stock_returns[t] = stock_returns.get(t, [])
                stock_returns[t].append(pnl)
                trade_returns.append(pnl)
                final_value += net_proceeds
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

        metrics = compute_metrics(ts_df["portfolio_value"], self.cfg.initial_capital, trade_returns, total_costs)

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

        data_quality = {
            "total_rebalances": len(rebalance_dates),
            "rebalances_skipped_no_data": periods_without_pit_data,
            "message": (
                f"{periods_without_pit_data} of {len(rebalance_dates)} rebalance periods had no "
                "fundamentals recorded from before that date, so the portfolio held cash instead "
                "of trading on stale/future data for those periods. This platform currently only "
                "stores a live snapshot of fundamentals at ingestion time, not true historical "
                "filings, so only rebalances on or after your data was ingested have real "
                "point-in-time fundamentals to trade on."
            ) if periods_without_pit_data > 0 else None,
        }

        return {
            "timeseries": result_ts.to_dict("records"),
            "rebalance_logs": rebalance_logs,
            "metrics": metrics,
            "benchmark": benchmark_metrics,
            "winners": winners,
            "losers": losers,
            "data_quality": data_quality,
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
            logger.exception("Failed loading price history for backtest")
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
            logger.exception("Failed loading fundamentals for backtest")
            return pd.DataFrame()

    def _get_benchmark_metrics(self):
        # Fetches directly from Yahoo's public chart endpoint rather than
        # yfinance's yf.download(): that call has no timeout and can hang
        # indefinitely if yfinance's own crumb/cookie session gets stuck (the
        # same failure mode that broke market-data ingestion — see
        # app/modules/market_data/fetcher.py). The chart endpoint needs no
        # crumb, so it isn't subject to that at all, and a bounded timeout
        # here means a slow/unreachable benchmark degrades to "no benchmark"
        # instead of hanging the whole backtest job.
        try:
            import requests
            from datetime import datetime, timezone

            period1 = int(datetime.combine(self.cfg.start_date, datetime.min.time(), tzinfo=timezone.utc).timestamp())
            period2 = int(datetime.combine(self.cfg.end_date, datetime.min.time(), tzinfo=timezone.utc).timestamp())

            resp = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI",
                params={"period1": period1, "period2": period2, "interval": "1d"},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=15,
            )
            if resp.status_code != 200:
                return None

            result = (resp.json().get("chart", {}).get("result") or [None])[0]
            if result is None:
                return None

            closes = (result.get("indicators", {}).get("quote") or [{}])[0].get("close") or []
            closes = [c for c in closes if c is not None]
            if not closes:
                return None

            values = pd.Series(closes)
            initial_value = float(values.iloc[0])

            from app.modules.backtest.engine.metrics import compute_metrics

            return compute_metrics(
                values,
                initial_value
            )

        except Exception:
            logger.exception("Failed fetching benchmark data")
            return None

    def _build_price_matrix(self, price_df: pd.DataFrame) -> pd.DataFrame:
        """date-indexed, ticker-columned adj_close matrix, forward-filled so
        every date carries each ticker's most recent known price. Built once
        per run so _get_prices_on() is an index search, not an O(rows) filter."""
        if price_df.empty:
            return pd.DataFrame()
        pivot = price_df.pivot_table(index="date", columns="ticker", values="adj_close", aggfunc="last")
        return pivot.sort_index().ffill()

    def _get_prices_on(self, price_matrix: pd.DataFrame, target_date: date) -> dict:
        # Get most recent price on or before target_date
        if price_matrix.empty:
            return {}
        pos = price_matrix.index.searchsorted(target_date, side="right") - 1
        if pos < 0:
            return {}
        return price_matrix.iloc[pos].dropna().to_dict()
