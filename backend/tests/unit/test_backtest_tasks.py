from app.modules.backtest import tasks as tasks_module
from app.modules.backtest.models import BacktestJob

VALID_REQUEST = {
    "start_date": "2020-01-01",
    "end_date": "2021-01-01",
    "initial_capital": 1_000_000,
    "portfolio_size": 20,
    "rebalance_freq": "quarterly",
    "position_sizing": "equal",
    "sizing_metric": None,
    "market_cap_min": None,
    "market_cap_max": None,
    "roce_min": None,
    "pat_positive": True,
    "rank_metrics": [],
    "commission_bps": 0,
    "slippage_pct": 0,
}


class FakeEngine:
    """Stands in for BacktestEngine so unit tests exercise the task's own
    control flow (status transitions, error handling) without running the
    real engine or touching the network."""

    result = {"timeseries": [], "rebalance_logs": [], "metrics": {}}

    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db

    def run(self):
        return FakeEngine.result


def _make_job(db_session, user, request=None):
    job = BacktestJob(user_id=user.id, status="pending", request=request or VALID_REQUEST)
    db_session.add(job)
    db_session.commit()
    return job


def test_run_backtest_task_marks_job_success(db_session, make_user, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    monkeypatch.setattr(tasks_module, "BacktestEngine", FakeEngine)
    FakeEngine.result = {"timeseries": [1, 2, 3], "rebalance_logs": [], "metrics": {"cagr": 0.1}}
    job = _make_job(db_session, make_user())

    tasks_module.run_backtest_task(job.id)

    db_session.refresh(job)
    assert job.status == "success"
    assert job.result["metrics"] == {"cagr": 0.1}
    assert job.completed_at is not None


def test_run_backtest_task_marks_job_failure_on_engine_error(db_session, make_user, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    monkeypatch.setattr(tasks_module, "BacktestEngine", FakeEngine)
    FakeEngine.result = {"error": "No price data found. Please run data ingestion first."}
    job = _make_job(db_session, make_user())

    tasks_module.run_backtest_task(job.id)

    db_session.refresh(job)
    assert job.status == "failure"
    assert "No price data" in job.error


def test_run_backtest_task_marks_job_failure_on_exception(db_session, make_user, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)

    class ExplodingEngine(FakeEngine):
        def run(self):
            raise ValueError("boom")

    monkeypatch.setattr(tasks_module, "BacktestEngine", ExplodingEngine)
    job = _make_job(db_session, make_user())

    tasks_module.run_backtest_task(job.id)

    db_session.refresh(job)
    assert job.status == "failure"
    assert "boom" in job.error


def test_run_backtest_task_missing_job_is_a_noop(db_session, patch_task_session):
    patch_task_session(tasks_module)

    # Should not raise even though job_id 99999 doesn't exist.
    tasks_module.run_backtest_task(99999)
