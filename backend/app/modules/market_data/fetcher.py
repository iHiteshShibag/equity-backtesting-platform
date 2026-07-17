import logging
import random
import time
from datetime import date, datetime, timezone
from urllib.parse import quote

import requests
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.modules.stocks.models import Stock, DailyPrice
from app.modules.market_data.universe import NIFTY100_TICKERS

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

# Yahoo's public chart endpoint returns OHLCV without needing a crumb/cookie
# negotiation, unlike the quoteSummary API that yfinance's .info uses — so it
# isn't subject to Yahoo throttling crumb issuance for a given source IP.
CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


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
        logger.info("Added %d stocks to registry", len(new_stocks))


def _backoff_sleep(attempt: int):
    time.sleep((2 ** attempt) + random.uniform(0, 1))


def _fetch_chart(ticker: str, period1: int, period2: int, max_retries=MAX_RETRIES):
    """Fetch one ticker's daily OHLCV with exponential-backoff retries.
    Returns the chart "result[0]" dict, or None if every attempt failed."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(
                CHART_URL.format(ticker=quote(ticker, safe="")),
                params={"period1": period1, "period2": period2, "interval": "1d"},
                headers=HEADERS,
                timeout=15,
            )
            if resp.status_code == 200:
                result = resp.json().get("chart", {}).get("result")
                if result:
                    return result[0]
            else:
                logger.warning(
                    "%s: HTTP %s on attempt %d/%d", ticker, resp.status_code, attempt + 1, max_retries
                )
        except Exception:
            logger.warning(
                "Chart fetch attempt %d/%d failed for %s", attempt + 1, max_retries, ticker, exc_info=True
            )
        if attempt < max_retries - 1:
            _backoff_sleep(attempt)
    return None


def fetch_and_store_prices(session: Session, start: str = "2015-01-01", end: str = None) -> dict:
    end = end or date.today().isoformat()
    period1 = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
    period2 = int(datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp())

    ensure_stocks_exist(session)
    ticker_map = {s.ticker: s.id for s in session.query(Stock).all()}

    rows = []
    succeeded = 0
    failed_tickers = []

    for idx, ticker in enumerate(NIFTY100_TICKERS):
        stock_id = ticker_map.get(ticker)
        if not stock_id:
            continue

        chart = _fetch_chart(ticker, period1, period2)
        if chart is None:
            failed_tickers.append(ticker)
            continue

        timestamps = chart.get("timestamp") or []
        quote = (chart.get("indicators", {}).get("quote") or [{}])[0]
        adjclose = (chart.get("indicators", {}).get("adjclose") or [{}])[0].get("adjclose") or []
        opens, highs, lows, closes, volumes = (
            quote.get("open") or [], quote.get("high") or [], quote.get("low") or [],
            quote.get("close") or [], quote.get("volume") or [],
        )

        ticker_rows = 0
        for i, ts in enumerate(timestamps):
            close = closes[i] if i < len(closes) else None
            if close is None:
                continue
            rows.append({
                "stock_id": stock_id,
                "date": datetime.fromtimestamp(ts, tz=timezone.utc).date(),
                "open": opens[i] if i < len(opens) else None,
                "high": highs[i] if i < len(highs) else None,
                "low": lows[i] if i < len(lows) else None,
                "close": close,
                "adj_close": adjclose[i] if i < len(adjclose) and adjclose[i] is not None else close,
                "volume": int(volumes[i]) if i < len(volumes) and volumes[i] is not None else None,
            })
            ticker_rows += 1

        if ticker_rows > 0:
            succeeded += 1
        else:
            failed_tickers.append(ticker)

        if (idx + 1) % 10 == 0:
            logger.info("Fetched %d/%d tickers", idx + 1, len(NIFTY100_TICKERS))
        time.sleep(0.3)

    if not rows:
        logger.warning("No price rows to insert")
        return {"succeeded": succeeded, "failed": len(failed_tickers), "failed_tickers": failed_tickers}

    chunk_size = 1000
    total = 0
    for i in range(0, len(rows), chunk_size):
        chunk = rows[i:i + chunk_size]
        stmt = pg_insert(DailyPrice.__table__).values(chunk)
        stmt = stmt.on_conflict_do_nothing(constraint="uq_price_stock_date")
        session.execute(stmt)
        session.commit()
        total += len(chunk)

    logger.info("Stored %d price rows. Succeeded=%d, Failed=%d", total, succeeded, len(failed_tickers))

    return {
        "succeeded": succeeded,
        "failed": len(failed_tickers),
        "failed_tickers": failed_tickers,
    }
