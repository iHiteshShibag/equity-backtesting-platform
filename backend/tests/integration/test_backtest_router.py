from datetime import date, timedelta

import pytest

from app.modules.backtest import router as backtest_router_module
from app.modules.stocks.models import Stock, Fundamental
from app.modules.market_data.models import IndexMembership

VALID_REQUEST = {"start_date": "2020-01-01", "end_date": "2021-01-01"}


@pytest.fixture(autouse=True)
def mock_backtest_delay(monkeypatch):
    """Route tests exercise job-queuing/ownership logic, not the Celery task
    body — real .delay() would try to reach a broker that doesn't exist here,
    and the task itself opens its own SessionLocal() bound to the real
    DATABASE_URL rather than this test's SQLite session. Task internals are
    covered separately in tests/unit/test_backtest_tasks.py."""
    calls = []

    class FakeAsyncResult:
        id = "fake-task-id"

    def fake_delay(job_id):
        calls.append(job_id)
        return FakeAsyncResult()

    monkeypatch.setattr(backtest_router_module.run_backtest_task, "delay", fake_delay)
    return calls


def test_run_backtest_queues_job_and_returns_202(make_user, make_client, mock_backtest_delay):
    user = make_user()
    client = make_client(user)

    response = client.post("/api/backtest/run", json=VALID_REQUEST)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert mock_backtest_delay == [body["id"]]


def test_run_backtest_rejected_without_tos_acceptance(make_user, make_client, mock_backtest_delay):
    user = make_user(tos_accepted=False)
    client = make_client(user)

    response = client.post("/api/backtest/run", json=VALID_REQUEST)

    assert response.status_code == 403
    assert mock_backtest_delay == []


def test_run_backtest_rejects_end_date_before_start_date(make_user, make_client, mock_backtest_delay):
    user = make_user()
    client = make_client(user)

    response = client.post(
        "/api/backtest/run",
        json={**VALID_REQUEST, "start_date": "2021-01-01", "end_date": "2020-01-01"},
    )

    assert response.status_code == 422


def test_run_backtest_rejects_non_positive_initial_capital(make_user, make_client, mock_backtest_delay):
    user = make_user()
    client = make_client(user)

    response = client.post(
        "/api/backtest/run",
        json={**VALID_REQUEST, "initial_capital": 0},
    )

    assert response.status_code == 422


def test_run_backtest_rejects_non_positive_portfolio_size(make_user, make_client, mock_backtest_delay):
    user = make_user()
    client = make_client(user)

    response = client.post(
        "/api/backtest/run",
        json={**VALID_REQUEST, "portfolio_size": -1},
    )

    assert response.status_code == 422


def test_get_own_job_succeeds(make_user, make_client, mock_backtest_delay):
    user = make_user()
    client = make_client(user)
    job_id = client.post("/api/backtest/run", json=VALID_REQUEST).json()["id"]

    response = client.get(f"/api/backtest/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id


def test_get_other_users_job_is_hidden(make_user, make_client, mock_backtest_delay):
    owner = make_user(email="owner@example.com")
    other = make_user(email="other@example.com")
    owner_client = make_client(owner)
    job_id = owner_client.post("/api/backtest/run", json=VALID_REQUEST).json()["id"]

    other_client = make_client(other)
    response = other_client.get(f"/api/backtest/jobs/{job_id}")

    assert response.status_code == 404


def test_admin_can_view_any_users_job(make_user, make_client, mock_backtest_delay):
    owner = make_user(email="owner@example.com", role="member")
    admin = make_user(email="admin@example.com", role="admin")
    owner_client = make_client(owner)
    job_id = owner_client.post("/api/backtest/run", json=VALID_REQUEST).json()["id"]

    admin_client = make_client(admin)
    response = admin_client.get(f"/api/backtest/jobs/{job_id}")

    assert response.status_code == 200


def test_get_nonexistent_job_returns_404(make_user, make_client):
    user = make_user()
    client = make_client(user)

    response = client.get("/api/backtest/jobs/99999")

    assert response.status_code == 404


def test_list_jobs_only_returns_own_jobs(make_user, make_client, mock_backtest_delay):
    user_a = make_user(email="a@example.com")
    user_b = make_user(email="b@example.com")
    client_a = make_client(user_a)
    client_b = make_client(user_b)
    client_a.post("/api/backtest/run", json=VALID_REQUEST)
    client_b.post("/api/backtest/run", json=VALID_REQUEST)

    response = client_a.get("/api/backtest/jobs")

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1


def _make_stock_with_fundamental(db_session, ticker, market_cap=None, roce=None, pat=None):
    stock = Stock(ticker=ticker, name=ticker, exchange="NSE")
    db_session.add(stock)
    db_session.flush()
    # Fundamental.id is a BigInteger PK -- SQLite only auto-assigns rowid for
    # an `INTEGER PRIMARY KEY` column, which SQLAlchemy maps from Integer, not
    # BigInteger, so it must be supplied explicitly here.
    next_id = (db_session.query(Fundamental).count()) + 1
    fund = Fundamental(
        id=next_id,
        stock_id=stock.id,
        report_date=date(2023, 3, 31),
        period_type="annual",
        market_cap=market_cap,
        roce=roce,
        pat=pat,
    )
    db_session.add(fund)
    db_session.commit()
    return stock


def test_universe_count_with_no_fundamentals_returns_zero(make_user, make_client):
    client = make_client(make_user())

    response = client.get("/api/backtest/universe-count")

    assert response.status_code == 200
    assert response.json() == {"matched": 0, "universe": 0}


def test_universe_count_applies_market_cap_filter(make_user, make_client, db_session):
    _make_stock_with_fundamental(db_session, "BIGCO", market_cap=50000)
    _make_stock_with_fundamental(db_session, "SMALLCO", market_cap=500)
    client = make_client(make_user())

    response = client.get("/api/backtest/universe-count", params={"market_cap_min": 1000})

    assert response.status_code == 200
    body = response.json()
    assert body == {"matched": 1, "universe": 2}


def test_universe_count_restricts_to_active_index_members(make_user, make_client, db_session):
    _make_stock_with_fundamental(db_session, "MEMBER", market_cap=1000)
    _make_stock_with_fundamental(db_session, "NONMEMBER", market_cap=1000)
    db_session.add(IndexMembership(
        index_name="NIFTY100", ticker="MEMBER",
        start_date=date.today() - timedelta(days=30), end_date=None,
    ))
    db_session.commit()
    client = make_client(make_user())

    response = client.get("/api/backtest/universe-count")

    assert response.status_code == 200
    assert response.json() == {"matched": 1, "universe": 1}


def test_universe_count_pat_positive_filter(make_user, make_client, db_session):
    _make_stock_with_fundamental(db_session, "PROFITABLE", market_cap=1000, pat=100)
    _make_stock_with_fundamental(db_session, "LOSSMAKING", market_cap=1000, pat=-50)
    client = make_client(make_user())

    response = client.get("/api/backtest/universe-count", params={"pat_positive": True})

    assert response.status_code == 200
    body = response.json()
    assert body == {"matched": 1, "universe": 2}
