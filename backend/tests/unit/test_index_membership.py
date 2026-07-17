from datetime import date

from app.modules.market_data.index_membership import get_active_tickers
from app.modules.market_data.models import IndexMembership


def _add(db_session, ticker, start_date, end_date=None, index_name="NIFTY100"):
    db_session.add(IndexMembership(index_name=index_name, ticker=ticker, start_date=start_date, end_date=end_date))
    db_session.commit()


def test_get_active_tickers_excludes_ticker_before_its_listing_date(db_session):
    _add(db_session, "NYKAA.NS", start_date=date(2021, 11, 10))

    before_listing = get_active_tickers(db_session, "NIFTY100", date(2020, 1, 1))
    after_listing = get_active_tickers(db_session, "NIFTY100", date(2022, 1, 1))

    assert "NYKAA.NS" not in before_listing
    assert "NYKAA.NS" in after_listing


def test_get_active_tickers_excludes_ticker_after_its_removal_date(db_session):
    _add(db_session, "OLDCO.NS", start_date=date(2015, 1, 1), end_date=date(2019, 12, 31))

    before_removal = get_active_tickers(db_session, "NIFTY100", date(2018, 1, 1))
    after_removal = get_active_tickers(db_session, "NIFTY100", date(2020, 1, 1))

    assert "OLDCO.NS" in before_removal
    assert "OLDCO.NS" not in after_removal


def test_get_active_tickers_null_end_date_means_still_a_member(db_session):
    _add(db_session, "RELIANCE.NS", start_date=date(2000, 1, 1), end_date=None)

    active = get_active_tickers(db_session, "NIFTY100", date(2026, 1, 1))

    assert "RELIANCE.NS" in active


def test_get_active_tickers_scoped_to_index_name(db_session):
    _add(db_session, "AAA.NS", start_date=date(2015, 1, 1), index_name="NIFTY100")
    _add(db_session, "BBB.NS", start_date=date(2015, 1, 1), index_name="SENSEX30")

    nifty_active = get_active_tickers(db_session, "NIFTY100", date(2020, 1, 1))

    assert "AAA.NS" in nifty_active
    assert "BBB.NS" not in nifty_active


def test_get_active_tickers_returns_empty_set_without_a_db_session():
    assert get_active_tickers(None, "NIFTY100", date(2020, 1, 1)) == set()
