import logging
import sys

from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging():
    """Route all app logs through a single JSON formatter on stdout, so log
    lines are directly queryable in any log aggregator without a parser."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        )
    )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.LOG_LEVEL)

    # uvicorn/celery configure their own handlers on import; force them onto
    # the same JSON formatter instead of their default plain-text ones.
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "celery", "celery.task"):
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False


def setup_sentry(**extra_integrations):
    """No-op when SENTRY_DSN is unset (e.g. local dev) — sentry_sdk.init
    treats an empty dsn as disabled, so callers never need to branch on it."""
    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN or None,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,
        **extra_integrations,
    )
