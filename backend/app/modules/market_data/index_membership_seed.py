# Manually-compiled, best-effort point-in-time NIFTY100 membership seed.
#
# This is NOT a licensed index-history feed and does NOT capture every
# historical addition/removal -- compiling the full reconstitution history
# for 100 tickers back to 2015 would require a paid index-data vendor. What
# it DOES capture reliably (public, easily verifiable IPO/listing dates) is
# the floor: a stock cannot have been a NIFTY100 member before it existed as
# a listed company. That alone fixes the most egregious survivorship-bias
# cases -- e.g. backtests currently treat NYKAA/PAYTM/ZOMATO as available
# NIFTY100 picks years before their IPOs.
#
# Every ticker in NIFTY100_TICKERS not listed below defaults to "member since
# DEFAULT_START_DATE" (i.e. the full backtest window) with no end_date --
# a safe no-op that avoids fabricating exclusions we can't verify.
#
# To extend: add a (ticker, start_date, end_date) row once you have a
# verified listing/reconstitution date. end_date=None means "still a member".

from datetime import date

DEFAULT_START_DATE = date(2000, 1, 1)

# Known IPO/listing dates for tickers in NIFTY100_TICKERS that listed well
# after 2015 (verified against NSE/BSE listing announcements).
KNOWN_LISTING_DATES: dict[str, date] = {
    "DMART.NS": date(2017, 3, 21),
    "ICICIPRULI.NS": date(2016, 9, 29),
    "SBILIFE.NS": date(2017, 10, 3),
    "HDFCLIFE.NS": date(2017, 11, 17),
    "AUBANK.NS": date(2017, 7, 10),
    "IRCTC.NS": date(2019, 10, 14),
    "IRFC.NS": date(2021, 1, 29),
    "ETERNAL.NS": date(2021, 7, 23),  # listed as Zomato
    "NYKAA.NS": date(2021, 11, 10),
    "PAYTM.NS": date(2021, 11, 18),  # One97 Communications
    "POLICYBZR.NS": date(2021, 11, 15),  # PB Fintech
}


def seed_rows(index_name: str, tickers: list[str]) -> list[dict]:
    rows = []
    for ticker in tickers:
        start = KNOWN_LISTING_DATES.get(ticker, DEFAULT_START_DATE)
        rows.append({"index_name": index_name, "ticker": ticker, "start_date": start, "end_date": None})
    return rows
