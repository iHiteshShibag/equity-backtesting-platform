import time
import yfinance as yf

from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.stock import Stock, Fundamental
from app.data.universe import NIFTY100_TICKERS

MAX_RETRIES = 3

def to_cr(val):
    if val is None:
        return None

    try:
        return round(float(val) / 1e7, 2)
    except Exception:
        return None


def fetch_fundamentals_yfinance(session: Session):
    ticker_map = {
        s.ticker: s
        for s in session.query(Stock).all()
    }

    success = 0
    failed = 0

    for ticker in NIFTY100_TICKERS:

        stock = ticker_map.get(ticker)

        if not stock:
            continue

        try:
            t = yf.Ticker(ticker)
            info = t.info

            market_cap = None

            try:
                fi = t.fast_info

                if isinstance(fi, dict):
                    market_cap = fi.get("market_cap")
                else:
                    market_cap = getattr(fi, "market_cap", None)

            except Exception:
                pass


            roe = None
            roe_raw = info.get("returnOnEquity")

            if roe_raw is not None:
                roe = round(float(roe_raw) * 100, 2)

            total_debt = to_cr(info.get("totalDebt"))
            total_equity = to_cr(info.get("bookValue"))

            debt_to_equity = None
            if total_debt and total_equity and total_equity != 0:
                debt_to_equity = round(total_debt / total_equity, 2)

            capital_employed = None
            if total_debt and total_equity:
                capital_employed = round(total_debt + total_equity, 2)

            row = {
                "stock_id": stock.id,
                "report_date": date.today(),
                "period_type": "annual",
                "fiscal_period": "latest",

                "market_cap": to_cr(info.get("marketCap")),

                "revenue": to_cr(info.get("totalRevenue")),
                "pat": to_cr(info.get("netIncomeToCommon")),
                "eps": info.get("trailingEps"),

                "total_assets": to_cr(info.get("totalAssets")),
                "total_equity": total_equity,
                "total_debt": total_debt,
                "capital_employed": capital_employed,

                "cfo": to_cr(info.get("operatingCashflow")),

                "pe_ratio": info.get("trailingPE"),
                "pb_ratio": info.get("priceToBook"),

                "roe": roe,
                "roce": None,

                "debt_to_equity": debt_to_equity,
            }

            stmt = pg_insert(
                Fundamental.__table__
            ).values([row])

            stmt = stmt.on_conflict_do_update(
                constraint="uq_fund_stock_date_type",
                set_={
                    k: v
                    for k, v in row.items()
                    if k not in (
                        "stock_id",
                        "report_date",
                        "period_type",
                    )
                }
            )

            session.execute(stmt)
            session.commit()

            success += 1

            print(
                f"✓ {ticker}: "
                f"{row['market_cap']} Cr"
            )

            time.sleep(1)

        except Exception as e:
            failed += 1

            session.rollback()

            print(
                f"✗ {ticker}: {e}"
            )

    print(
        f"\nCompleted. "
        f"Success={success}, Failed={failed}"
    )

