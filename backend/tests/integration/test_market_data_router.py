from datetime import datetime, timedelta, timezone

import pytest

from app.modules.market_data import router as market_data_router_module
from app.modules.market_data.models import IngestionRun


@pytest.fixture(autouse=True)
def mock_ingestion_delay(monkeypatch):
    """Same rationale as test_backtest_router's mock_backtest_delay — avoid a
    real Celery broker/DB dependency for router-level tests."""
    calls = []

    class FakeAsyncResult:
        id = "fake-task-id"

    def fake_delay(trigger):
        calls.append(trigger)
        return FakeAsyncResult()

    monkeypatch.setattr(market_data_router_module.run_ingestion_task, "delay", fake_delay)
    return calls


def test_status_with_no_runs_yet(make_user, make_client):
    client = make_client(make_user())

    response = client.get("/api/market-data/status")

    assert response.status_code == 200
    body = response.json()
    assert body["is_empty"] is True
    assert body["latest_run"] is None
    assert body["recent_runs"] == []


def test_trigger_ingestion_queues_task(make_user, make_client, mock_ingestion_delay):
    client = make_client(make_user())

    response = client.post("/api/market-data/ingest")

    assert response.status_code == 200
    assert mock_ingestion_delay == ["manual"]


def test_trigger_ingestion_while_running_is_rejected(make_user, make_client, db_session, mock_ingestion_delay):
    client = make_client(make_user())
    db_session.add(IngestionRun(trigger="scheduled", status="running"))
    db_session.commit()

    response = client.post("/api/market-data/ingest")

    assert response.status_code == 409
    assert mock_ingestion_delay == []


def test_trigger_ingestion_supersedes_stale_running_run(make_user, make_client, db_session, mock_ingestion_delay):
    """A run stuck in "running" past the staleness threshold was orphaned by
    a worker crash/restart — it must not block new runs forever."""
    client = make_client(make_user())
    stale_started_at = datetime.now(timezone.utc) - timedelta(hours=3)
    stale_run = IngestionRun(trigger="scheduled", status="running", started_at=stale_started_at)
    db_session.add(stale_run)
    db_session.commit()

    response = client.post("/api/market-data/ingest")

    assert response.status_code == 200
    assert mock_ingestion_delay == ["manual"]
    db_session.refresh(stale_run)
    assert stale_run.status == "failure"
    assert stale_run.error is not None


def test_status_reports_latest_and_recent_runs(make_user, make_client, db_session):
    client = make_client(make_user())
    now = datetime.now(timezone.utc)
    # Explicit, clearly-separated timestamps — relying on insertion order for
    # tie-breaking would be flaky since started_at's default (func.now()) has
    # only second-level resolution on SQLite.
    older = IngestionRun(
        trigger="scheduled", status="success", prices_success=100, prices_failed=0,
        started_at=now - timedelta(hours=1),
    )
    db_session.add(older)
    db_session.commit()
    newer = IngestionRun(
        trigger="manual", status="partial", prices_success=90, prices_failed=10,
        started_at=now,
    )
    db_session.add(newer)
    db_session.commit()

    response = client.get("/api/market-data/status")

    assert response.status_code == 200
    body = response.json()
    assert body["latest_run"]["id"] == newer.id
    assert body["latest_run"]["status"] == "partial"
    assert [r["id"] for r in body["recent_runs"]] == [newer.id, older.id]
