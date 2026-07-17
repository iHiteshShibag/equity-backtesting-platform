import logging
from datetime import date

from app.core.email import send_email
from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.backtest.engine.backtest_engine import BacktestConfig, BacktestEngine
from app.modules.strategies.models import SavedStrategy
from app.modules.strategies.router import _next_rebalance_date
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="strategies.check_due")
def check_due_strategies() -> None:
    """Runs daily via celery-beat. For every active saved strategy whose
    next_rebalance_date has arrived, re-runs the backtest through today and
    emails the owner a summary, then advances the schedule."""
    db = SessionLocal()
    try:
        today = date.today()
        due = (
            db.query(SavedStrategy)
            .filter(SavedStrategy.is_active.is_(True))
            .filter(SavedStrategy.next_rebalance_date <= today)
            .all()
        )
        logger.info("Checking due strategies", extra={"count": len(due)})

        for strategy in due:
            try:
                _process_due_strategy(db, strategy, today)
            except Exception:
                logger.exception("Failed processing saved strategy", extra={"strategy_id": strategy.id})
    finally:
        db.close()


def _process_due_strategy(db, strategy: SavedStrategy, today: date) -> None:
    req = dict(strategy.request)
    req["end_date"] = today.isoformat()

    cfg = BacktestConfig.from_request_dict(req)
    result = BacktestEngine(cfg, db).run()

    user = db.query(User).filter(User.id == strategy.user_id).first()
    if user is not None:
        if "error" in result:
            body = f"Your saved strategy '{strategy.name}' hit its rebalance date but failed to run:\n{result['error']}"
        else:
            metrics = result.get("metrics", {})
            body = (
                f"Rebalance due for saved strategy '{strategy.name}'.\n\n"
                f"CAGR: {metrics.get('cagr', 0):.2%}\n"
                f"Sharpe: {metrics.get('sharpe', 0):.2f}\n"
                f"Max Drawdown: {metrics.get('max_drawdown', 0):.2%}\n"
                f"Final Value: {metrics.get('final_value', 0):,.2f}\n\n"
                "Log in to view full holdings and rebalance details."
            )
        send_email(user.email, f"[Equity Backtesting] Rebalance due: {strategy.name}", body)

    strategy.next_rebalance_date = _next_rebalance_date(strategy.rebalance_freq, today)
    db.commit()
