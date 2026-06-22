import yfinance as yf
import pandas as pd
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.stock import Stock, DailyPrice
from app.data.universe import NIFTY100_TICKERS


def ensure_stocks_exist(session: Session):
    """Create stock records if they don't exist."""
    existing = {s.ticker for s in session.query(Stock.ticker).all()}
    new_stocks = []
    for ticker in NIFTY100_TICKERS:
        if ticker not in existing:
            new_stocks.append(Stock(
                ticker=ticker,
                name=ticker.replace(".NS", "").replace(".BO", ""),
                exchange="NSE" if ticker.endswith(".NS") else "BSE",
            ))
    if new_stocks:
        session.bulk_save_objects(new_stocks)
        session.commit()
        print(f"  Added {len(new_stocks)} stocks to registry")


def fetch_and_store_prices(session: Session, start: str = "2015-01-01", end: str = None):
    import time

    end = end or date.today().isoformat()

    ensure_stocks_exist(session)

    ticker_map = {
        s.ticker: s.id
        for s in session.query(Stock).all()
    }

    all_frames = {}

    BATCH_SIZE = 10

    for i in range(0, len(NIFTY100_TICKERS), BATCH_SIZE):

        batch = NIFTY100_TICKERS[i:i + BATCH_SIZE]

        print(
            f"  Downloading batch {i // BATCH_SIZE + 1}"
            f"/{(len(NIFTY100_TICKERS)-1)//BATCH_SIZE + 1}"
        )

        try:

            batch_data = yf.download(
                batch,
                start=start,
                end=end,
                group_by="ticker",
                auto_adjust=True,
                threads=False,
                progress=False,
            )

            for ticker in batch:
                try:
                    all_frames[ticker] = batch_data[ticker]
                except Exception:
                    pass

            time.sleep(3)

        except Exception as e:
            print(f"Batch failed: {e}")

    rows = []

    for ticker in NIFTY100_TICKERS:

        stock_id = ticker_map.get(ticker)

        if not stock_id:
            continue

        try:
            df = all_frames.get(ticker)

            if df is None:
                continue

            df = df.dropna(subset=["Close"]).reset_index()

        except Exception:
            continue

        for _, r in df.iterrows():

            rows.append({
                "stock_id": stock_id,
                "date": r["Date"].date()
                    if hasattr(r["Date"], "date")
                    else r["Date"],
                "open": float(r["Open"])
                    if pd.notna(r.get("Open"))
                    else None,
                "high": float(r["High"])
                    if pd.notna(r.get("High"))
                    else None,
                "low": float(r["Low"])
                    if pd.notna(r.get("Low"))
                    else None,
                "close": float(r["Close"]),
                "adj_close": float(r["Close"]),
                "volume": int(r["Volume"])
                    if pd.notna(r.get("Volume"))
                    else None,
            })

    if not rows:
        print("No price rows to insert")
        return

    chunk_size = 1000
    total = 0

    for i in range(0, len(rows), chunk_size):

        chunk = rows[i:i + chunk_size]

        stmt = pg_insert(
            DailyPrice.__table__
        ).values(chunk)

        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_price_stock_date"
        )

        session.execute(stmt)
        session.commit()

        total += len(chunk)

    print(f"Stored {total} price rows")