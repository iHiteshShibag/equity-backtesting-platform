import logging
from datetime import datetime

from app.worker import celery_app
from app.db.session import SessionLocal
from app.modules.market_data.models import IngestionRun
from app.modules.market_data.fetcher import fetch_and_store_prices
from app.modules.market_data.fundamentals_screener import fetch_fundamentals_screener

logger = logging.getLogger(__name__)


@celery_app.task(name="market_data.ingest")
def run_ingestion_task(trigger: str = "manual") -> int:
    db = SessionLocal()
    try:
        run = IngestionRun(trigger=trigger, status="running", step="Fetching historical price data")
        db.add(run)
        db.commit()
        logger.info("Ingestion run started", extra={"run_id": run.id, "trigger": trigger})

        try:
            price_result = fetch_and_store_prices(db, start="2015-01-01")
            run.prices_success = price_result["succeeded"]
            run.prices_failed = price_result["failed"]
            run.prices_failed_tickers = price_result.get("failed_tickers", [])
            run.step = "Fetching fundamental data"
            db.commit()
            logger.info(
                "Price ingestion complete",
                extra={
                    "run_id": run.id,
                    "succeeded": run.prices_success,
                    "failed": run.prices_failed,
                    "failed_tickers": price_result.get("failed_tickers", []),
                },
            )

            fund_result = fetch_fundamentals_screener(db)
            run.funds_success = fund_result["succeeded"]
            run.funds_failed = fund_result["failed"]
            run.funds_failed_tickers = fund_result.get("failed_tickers", [])
            logger.info(
                "Fundamentals ingestion complete",
                extra={
                    "run_id": run.id,
                    "succeeded": run.funds_success,
                    "failed": run.funds_failed,
                    "failed_tickers": fund_result.get("failed_tickers", []),
                },
            )

            total_failed = run.prices_failed + run.funds_failed
            if total_failed == 0:
                run.status = "success"
            elif run.prices_success == 0 and run.funds_success == 0:
                run.status = "failure"
            else:
                run.status = "partial"
            run.step = "Complete"

        except Exception as e:
            run.status = "failure"
            run.error = str(e)
            run.step = "Failed"
            logger.exception("Ingestion run crashed", extra={"run_id": run.id})

        run.finished_at = datetime.utcnow()
        db.commit()
        logger.info("Ingestion run finished", extra={"run_id": run.id, "status": run.status})
        return run.id
    finally:
        db.close()
