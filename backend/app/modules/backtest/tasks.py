import logging
from datetime import datetime

from app.worker import celery_app
from app.db.session import SessionLocal
from app.modules.backtest.models import BacktestJob
from app.modules.backtest.engine.backtest_engine import BacktestEngine, BacktestConfig

logger = logging.getLogger(__name__)


@celery_app.task(name="backtest.run")
def run_backtest_task(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
        if job is None:
            logger.warning("Backtest job not found", extra={"job_id": job_id})
            return

        logger.info("Backtest job started", extra={"job_id": job_id, "user_id": job.user_id})
        job.status = "running"
        db.commit()

        try:
            cfg = BacktestConfig.from_request_dict(job.request)
            engine = BacktestEngine(cfg, db)
            result = engine.run()

            if "error" in result:
                job.status = "failure"
                job.error = result["error"]
            else:
                job.status = "success"
                job.result = result
        except Exception as e:
            job.status = "failure"
            job.error = str(e)
            logger.exception("Backtest job crashed", extra={"job_id": job_id})

        job.completed_at = datetime.utcnow()
        db.commit()
        logger.info(
            "Backtest job finished",
            extra={"job_id": job_id, "status": job.status},
        )
    finally:
        db.close()
