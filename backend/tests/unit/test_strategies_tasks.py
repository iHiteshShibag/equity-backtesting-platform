from datetime import date, timedelta

from app.modules.strategies import tasks as tasks_module
from app.modules.strategies.models import SavedStrategy

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
    """Stands in for BacktestEngine -- see the identical pattern/rationale in
    tests/unit/test_backtest_tasks.py."""

    result = {"timeseries": [], "rebalance_logs": [], "metrics": {"cagr": 0.1, "sharpe": 1.2,
                                                                    "max_drawdown": -0.05, "final_value": 1_100_000}}

    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db

    def run(self):
        return FakeEngine.result


def _make_strategy(db_session, user, next_rebalance_date, is_active=True):
    strategy = SavedStrategy(
        user_id=user.id,
        name="Test Strategy",
        request=VALID_REQUEST,
        rebalance_freq="quarterly",
        next_rebalance_date=next_rebalance_date,
        is_active=is_active,
    )
    db_session.add(strategy)
    db_session.commit()
    return strategy


def test_check_due_strategies_advances_schedule_and_sends_email(db_session, make_user, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    monkeypatch.setattr(tasks_module, "BacktestEngine", FakeEngine)
    FakeEngine.result = {"timeseries": [], "rebalance_logs": [], "metrics": {"cagr": 0.1, "sharpe": 1.2,
                                                                              "max_drawdown": -0.05, "final_value": 1_100_000}}
    sent = []
    monkeypatch.setattr(tasks_module, "send_email", lambda to, subject, body: sent.append((to, subject, body)))

    user = make_user(email="owner@example.com")
    strategy = _make_strategy(db_session, user, date.today() - timedelta(days=1))

    tasks_module.check_due_strategies()

    db_session.refresh(strategy)
    assert strategy.next_rebalance_date > date.today()
    assert len(sent) == 1
    assert sent[0][0] == "owner@example.com"
    assert "Test Strategy" in sent[0][1]


def test_check_due_strategies_skips_inactive(db_session, make_user, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    monkeypatch.setattr(tasks_module, "BacktestEngine", FakeEngine)
    sent = []
    monkeypatch.setattr(tasks_module, "send_email", lambda to, subject, body: sent.append((to, subject, body)))

    user = make_user()
    strategy = _make_strategy(db_session, user, date.today() - timedelta(days=1), is_active=False)

    tasks_module.check_due_strategies()

    db_session.refresh(strategy)
    assert strategy.next_rebalance_date == date.today() - timedelta(days=1)
    assert sent == []


def test_check_due_strategies_skips_not_yet_due(db_session, make_user, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)
    monkeypatch.setattr(tasks_module, "BacktestEngine", FakeEngine)
    sent = []
    monkeypatch.setattr(tasks_module, "send_email", lambda to, subject, body: sent.append((to, subject, body)))

    user = make_user()
    future = date.today() + timedelta(days=30)
    strategy = _make_strategy(db_session, user, future)

    tasks_module.check_due_strategies()

    db_session.refresh(strategy)
    assert strategy.next_rebalance_date == future
    assert sent == []


def test_check_due_strategies_emails_failure_reason_on_engine_error(db_session, make_user, patch_task_session, monkeypatch):
    patch_task_session(tasks_module)

    class FailingEngine(FakeEngine):
        def run(self):
            return {"error": "No price data found."}

    monkeypatch.setattr(tasks_module, "BacktestEngine", FailingEngine)
    sent = []
    monkeypatch.setattr(tasks_module, "send_email", lambda to, subject, body: sent.append((to, subject, body)))

    user = make_user(email="owner@example.com")
    _make_strategy(db_session, user, date.today())

    tasks_module.check_due_strategies()

    assert len(sent) == 1
    assert "failed" in sent[0][2].lower()
