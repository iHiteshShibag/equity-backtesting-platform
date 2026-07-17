import calendar
import logging
import time
from datetime import date

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.modules.stocks.models import Stock, Fundamental
from app.modules.market_data.universe import NIFTY100_TICKERS

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

# Same rationale as fetcher.py's CIRCUIT_BREAKER_CONSECUTIVE_FAILURES: past
# this many consecutive per-ticker failures, screener.in itself is almost
# certainly blocking/down -- stop early rather than burning through the rest
# of the universe against a dead source.
CIRCUIT_BREAKER_CONSECUTIVE_FAILURES = 15

BASE_URL = "https://www.screener.in/company/{ticker}/{view}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Consolidated financials are stale/absent for some companies (e.g. PSUs without
# subsidiaries) -- if the most recent period on that view is older than this,
# fall back to the standalone view instead.
MAX_STALENESS_YEARS = 2

FISCAL_MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}


def _parse_number(text):
    """'374,372' -> 374372.0, '10%' -> 10.0, '' or '-' -> None."""
    if text is None:
        return None
    cleaned = text.strip().replace(",", "").replace("%", "")
    if not cleaned or cleaned == "-":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_period_label(label):
    """'Mar 2024' -> date(2024, 3, 31). Non-period columns (e.g. 'TTM') -> None."""
    parts = label.strip().split()
    if len(parts) != 2 or parts[0] not in FISCAL_MONTHS:
        return None
    try:
        year = int(parts[1])
    except ValueError:
        return None
    month = FISCAL_MONTHS[parts[0]]
    return date(year, month, calendar.monthrange(year, month)[1])


def _section_table(soup, section_id):
    section = soup.find("section", {"id": section_id})
    return section.find("table") if section else None


def _extract_periods(table):
    """[(column_index, date), ...] for header columns that parse as a fiscal period."""
    if table is None:
        return []
    thead = table.find("thead")
    if thead is None:
        return []
    header_cells = [c.get_text(strip=True) for c in thead.find_all(["th", "td"])][1:]
    periods = []
    for i, label in enumerate(header_cells):
        parsed = parse_period_label(label)
        if parsed:
            periods.append((i, parsed))
    return periods


def _extract_row(table, label):
    """Cell texts (excluding the row-label cell) for the row matching `label`,
    ignoring screener's trailing '+' expand marker. None if the row isn't found."""
    if table is None:
        return None
    tbody = table.find("tbody") or table
    for tr in tbody.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if not cells:
            continue
        row_label = cells[0].get_text(strip=True).rstrip("+").strip()
        if row_label == label:
            return [c.get_text(strip=True) for c in cells[1:]]
    return None


def _cell(row, idx):
    if row is None or idx >= len(row):
        return None
    return _parse_number(row[idx])


def parse_current_market_cap(soup):
    """Market Cap from the top ratio bar, already in Cr (screener's native unit).
    This is always "now", not point-in-time -- screener doesn't publish a
    historical market-cap-by-year series."""
    top = soup.find("ul", {"id": "top-ratios"})
    if not top:
        return None
    for li in top.find_all("li"):
        name_el = li.find(class_="name")
        if name_el and name_el.get_text(strip=True) == "Market Cap":
            number_el = li.find(class_="number")
            return _parse_number(number_el.get_text(strip=True)) if number_el else None
    return None


def parse_historical_fundamentals(soup):
    """Parse a screener.in company page into one dict per fiscal year found in
    the Profit & Loss table. Figures are already in Cr on screener -- no
    to-Cr scaling needed here, unlike the old Yahoo quoteSummary path."""
    if soup is None:
        return []

    pl_table = _section_table(soup, "profit-loss")
    periods = _extract_periods(pl_table)
    if not periods:
        return []

    bs_table = _section_table(soup, "balance-sheet")
    ratios_table = _section_table(soup, "ratios")

    sales_row = _extract_row(pl_table, "Sales")
    net_profit_row = _extract_row(pl_table, "Net Profit")
    eps_row = _extract_row(pl_table, "EPS in Rs")

    equity_capital_row = _extract_row(bs_table, "Equity Capital")
    reserves_row = _extract_row(bs_table, "Reserves")
    borrowings_row = _extract_row(bs_table, "Borrowings")
    total_assets_row = _extract_row(bs_table, "Total Assets")

    roce_row = _extract_row(ratios_table, "ROCE %")

    market_cap = parse_current_market_cap(soup)

    rows = []
    for idx, report_date in periods:
        pat = _cell(net_profit_row, idx)
        equity_capital = _cell(equity_capital_row, idx)
        reserves = _cell(reserves_row, idx)
        total_debt = _cell(borrowings_row, idx)

        total_equity = None
        if equity_capital is not None and reserves is not None:
            total_equity = round(equity_capital + reserves, 2)

        capital_employed = None
        if total_debt is not None and total_equity is not None:
            capital_employed = round(total_debt + total_equity, 2)

        roe = round((pat / total_equity) * 100, 2) if pat is not None and total_equity else None
        debt_to_equity = round(total_debt / total_equity, 2) if total_debt is not None and total_equity else None

        rows.append({
            "report_date": report_date,
            "fiscal_period": report_date.strftime("%b %Y"),
            "revenue": _cell(sales_row, idx),
            "pat": pat,
            "eps": _cell(eps_row, idx),
            "total_assets": _cell(total_assets_row, idx),
            "total_equity": total_equity,
            "total_debt": total_debt,
            "capital_employed": capital_employed,
            "roe": roe,
            "roce": _cell(roce_row, idx),
            "debt_to_equity": debt_to_equity,
            "market_cap": market_cap,
        })
    return rows


def _is_recent_enough(periods, today):
    if not periods:
        return False
    return max(d.year for _, d in periods) >= today.year - MAX_STALENESS_YEARS


def _fetch_page(http_session, ticker, view, max_retries=MAX_RETRIES):
    url = BASE_URL.format(ticker=ticker, view=view)
    last_error = None
    for attempt in range(max_retries):
        try:
            resp = http_session.get(url, timeout=15)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "html.parser")
            if resp.status_code == 404:
                return None
            last_error = ValueError(f"HTTP {resp.status_code}")
        except Exception as e:
            last_error = e
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    if last_error:
        raise last_error
    return None


def fetch_company_page(http_session, screener_symbol, today=None):
    """Prefer consolidated financials; fall back to standalone when consolidated
    is missing or stale (e.g. PSUs without subsidiaries only keep standalone
    current -- see fetch_fundamentals_screener's MOIL case in tests)."""
    today = today or date.today()
    soup = _fetch_page(http_session, screener_symbol, "consolidated/")
    periods = _extract_periods(_section_table(soup, "profit-loss")) if soup else []
    if not _is_recent_enough(periods, today):
        standalone_soup = _fetch_page(http_session, screener_symbol, "")
        if standalone_soup is not None:
            return standalone_soup
    return soup


def fetch_fundamentals_screener(session: Session) -> dict:
    ticker_map = {s.ticker: s for s in session.query(Stock).all()}

    http_session = requests.Session()
    http_session.headers.update(HEADERS)

    success = 0
    failed_tickers = []
    consecutive_failures = 0
    aborted = False

    for ticker in NIFTY100_TICKERS:
        stock = ticker_map.get(ticker)
        if not stock:
            continue

        screener_symbol = ticker.replace(".NS", "").replace(".BO", "")

        try:
            soup = fetch_company_page(http_session, screener_symbol)
            historical_rows = parse_historical_fundamentals(soup)
            if not historical_rows:
                raise ValueError("no historical fundamentals parsed")

            for row in historical_rows:
                values = {"stock_id": stock.id, "period_type": "annual", **row}
                stmt = pg_insert(Fundamental.__table__).values([values])
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_fund_stock_date_type",
                    set_={k: v for k, v in values.items() if k not in ("stock_id", "report_date", "period_type")},
                )
                session.execute(stmt)

            session.commit()
            success += 1
            consecutive_failures = 0
            logger.info("%s: %d historical periods", ticker, len(historical_rows))

            time.sleep(0.5)

        except Exception:
            failed_tickers.append(ticker)
            session.rollback()
            logger.warning("Failed fetching fundamentals for %s", ticker, exc_info=True)
            consecutive_failures += 1
            if consecutive_failures >= CIRCUIT_BREAKER_CONSECUTIVE_FAILURES:
                logger.error(
                    "Aborting fundamentals ingestion after %d consecutive "
                    "failures (last ticker: %s) -- source likely blocking/down",
                    consecutive_failures, ticker,
                )
                aborted = True
                break

    logger.info("Completed. Success=%d, Failed=%d, Aborted=%s", success, len(failed_tickers), aborted)

    return {
        "succeeded": success,
        "failed": len(failed_tickers),
        "failed_tickers": failed_tickers,
        "aborted": aborted,
    }
