from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.core.observability import setup_logging, setup_sentry

# Every model must be imported here so SQLAlchemy can resolve cross-module
# foreign keys (e.g. backtest_jobs.user_id -> users.id) inside the worker
# process, which never goes through FastAPI's app startup.
from app.modules.auth.models import User  # noqa: F401
from app.modules.backtest.models import BacktestJob  # noqa: F401
from app.modules.stocks.models import Stock, DailyPrice, Fundamental  # noqa: F401
from app.modules.market_data.models import IngestionRun  # noqa: F401
from app.modules.strategies.models import SavedStrategy  # noqa: F401
from app.modules.orgs.models import Organization  # noqa: F401

setup_logging()
setup_sentry()

celery_app = Celery(
    "equity_backtesting",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    # Ingestion (slow, scheduled, I/O-bound scraping) and backtests (user-facing,
    # latency-sensitive) run on separate queues so a long ingestion run can't
    # starve backtest jobs waiting behind it -- each queue's workers scale
    # independently (see docker-compose.yml's celery-worker-* services).
    task_routes={
        "market_data.ingest": {"queue": "ingestion"},
        "backtest.run": {"queue": "backtest"},
        "strategies.check_due": {"queue": "backtest"},
    },
    task_default_queue="backtest",
    beat_schedule={
        # NSE closes 15:30 IST (10:00 UTC); run with a buffer for
        # end-of-day settlement, weekdays only.
        "daily-market-data-ingestion": {
            "task": "market_data.ingest",
            "schedule": crontab(hour=11, minute=0, day_of_week="1-5"),
            "kwargs": {"trigger": "scheduled"},
        },
        # Runs after ingestion completes so due strategies re-run against
        # the freshest prices/fundamentals.
        "daily-saved-strategy-check": {
            "task": "strategies.check_due",
            "schedule": crontab(hour=12, minute=0, day_of_week="1-5"),
        },
    },
)

celery_app.autodiscover_tasks(["app.modules.backtest", "app.modules.market_data", "app.modules.strategies"])
