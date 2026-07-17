from app.modules.market_data import tasks as tasks_module


class _FakeSentry:
    def __init__(self):
        self.messages = []
        self.exceptions = []

    def capture_message(self, message, level=None):
        self.messages.append((message, level))

    def capture_exception(self, exc):
        self.exceptions.append(exc)


def test_run_ingestion_task_success_when_nothing_fails(db_session, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    monkeypatch.setattr(tasks_module, "fetch_and_store_prices", lambda db, start: {"succeeded": 100, "failed": 0})
    monkeypatch.setattr(tasks_module, "fetch_fundamentals_screener", lambda db: {"succeeded": 100, "failed": 0})

    run_id = tasks_module.run_ingestion_task(trigger="manual")

    run = db_session.query(tasks_module.IngestionRun).filter_by(id=run_id).one()
    assert run.status == "success"
    assert run.prices_success == 100
    assert run.funds_success == 100
    assert run.finished_at is not None


def test_run_ingestion_task_partial_when_some_tickers_fail(db_session, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    monkeypatch.setattr(
        tasks_module, "fetch_and_store_prices",
        lambda db, start: {"succeeded": 90, "failed": 10, "failed_tickers": ["FOO.NS", "BAR.NS"]},
    )
    monkeypatch.setattr(
        tasks_module, "fetch_fundamentals_screener",
        lambda db: {"succeeded": 95, "failed": 5, "failed_tickers": ["FOO.NS"]},
    )

    run_id = tasks_module.run_ingestion_task(trigger="scheduled")

    run = db_session.query(tasks_module.IngestionRun).filter_by(id=run_id).one()
    assert run.status == "partial"
    assert run.trigger == "scheduled"
    assert run.prices_failed_tickers == ["FOO.NS", "BAR.NS"]
    assert run.funds_failed_tickers == ["FOO.NS"]


def test_run_ingestion_task_failure_when_everything_fails(db_session, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    monkeypatch.setattr(tasks_module, "fetch_and_store_prices", lambda db, start: {"succeeded": 0, "failed": 105})
    monkeypatch.setattr(tasks_module, "fetch_fundamentals_screener", lambda db: {"succeeded": 0, "failed": 105})

    run_id = tasks_module.run_ingestion_task(trigger="manual")

    run = db_session.query(tasks_module.IngestionRun).filter_by(id=run_id).one()
    assert run.status == "failure"


def test_run_ingestion_task_failure_on_exception(db_session, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    fake_sentry = _FakeSentry()
    monkeypatch.setattr(tasks_module, "sentry_sdk", fake_sentry)

    def boom(db, start):
        raise ConnectionError("network unreachable")

    monkeypatch.setattr(tasks_module, "fetch_and_store_prices", boom)

    run_id = tasks_module.run_ingestion_task(trigger="manual")

    run = db_session.query(tasks_module.IngestionRun).filter_by(id=run_id).one()
    assert run.status == "failure"
    assert "network unreachable" in run.error
    assert len(fake_sentry.exceptions) == 1


def test_run_ingestion_task_alerts_sentry_on_circuit_breaker_abort(db_session, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    fake_sentry = _FakeSentry()
    monkeypatch.setattr(tasks_module, "sentry_sdk", fake_sentry)
    monkeypatch.setattr(
        tasks_module, "fetch_and_store_prices",
        lambda db, start: {"succeeded": 0, "failed": 15, "failed_tickers": [], "aborted": True},
    )
    monkeypatch.setattr(
        tasks_module, "fetch_fundamentals_screener",
        lambda db: {"succeeded": 0, "failed": 0, "failed_tickers": []},
    )

    run_id = tasks_module.run_ingestion_task(trigger="scheduled")

    run = db_session.query(tasks_module.IngestionRun).filter_by(id=run_id).one()
    assert "circuit breaker" in run.error.lower()
    assert len(fake_sentry.messages) == 1
    assert fake_sentry.messages[0][1] == "error"


def test_run_ingestion_task_does_not_alert_sentry_on_ordinary_partial_run(db_session, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    fake_sentry = _FakeSentry()
    monkeypatch.setattr(tasks_module, "sentry_sdk", fake_sentry)
    monkeypatch.setattr(
        tasks_module, "fetch_and_store_prices",
        lambda db, start: {"succeeded": 90, "failed": 10, "failed_tickers": []},
    )
    monkeypatch.setattr(
        tasks_module, "fetch_fundamentals_screener",
        lambda db: {"succeeded": 95, "failed": 5, "failed_tickers": []},
    )

    tasks_module.run_ingestion_task(trigger="scheduled")

    assert fake_sentry.messages == []
    assert fake_sentry.exceptions == []
