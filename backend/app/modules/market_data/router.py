from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.db.session import get_db
from app.modules.auth.deps import get_current_user
from app.modules.stocks.models import Stock, DailyPrice, Fundamental
from app.modules.market_data.models import IngestionRun
from app.modules.market_data.tasks import run_ingestion_task

router = APIRouter(prefix="/api/market-data", tags=["market-data"], dependencies=[Depends(get_current_user)])

# A full run (100+ tickers, retries included) normally finishes in well under
# an hour; anything still "running" past this was orphaned by a worker
# crash/restart mid-task and shouldn't block new runs forever.
STALE_RUN_THRESHOLD = timedelta(hours=2)


def _to_run_out(run: IngestionRun) -> dict:
    return {
        "id": run.id,
        "trigger": run.trigger,
        "status": run.status,
        "step": run.step,
        "prices_success": run.prices_success,
        "prices_failed": run.prices_failed,
        "prices_failed_tickers": run.prices_failed_tickers or [],
        "funds_success": run.funds_success,
        "funds_failed": run.funds_failed,
        "funds_failed_tickers": run.funds_failed_tickers or [],
        "error": run.error,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
    }


@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    """Report DB row counts plus the latest ingestion run and recent history."""
    stock_count = db.query(Stock).count()
    price_count = db.query(DailyPrice).count()
    fundamental_count = db.query(Fundamental).count()

    runs = (
        db.query(IngestionRun)
        .order_by(IngestionRun.started_at.desc())
        .limit(10)
        .all()
    )

    return {
        "is_empty": price_count == 0,
        "counts": {
            "stocks": stock_count,
            "prices": price_count,
            "fundamentals": fundamental_count,
        },
        "latest_run": _to_run_out(runs[0]) if runs else None,
        "recent_runs": [_to_run_out(r) for r in runs],
        # Matches the crontab in app/worker.py — NSE close (15:30 IST) + buffer, weekdays.
        "schedule": "Weekdays at 16:30 IST",
    }


@router.post("/ingest")
@limiter.limit("5/minute")
def trigger_ingestion(request: Request, db: Session = Depends(get_db)):
    """Queue a manual data ingestion run (prices + fundamentals)."""
    # FOR UPDATE so two concurrent calls can't both read "no running run" and
    # both queue a job -- the second call blocks here until the first
    # transaction commits/rolls back, then re-reads the now-committed state.
    running = (
        db.query(IngestionRun)
        .filter(IngestionRun.status == "running")
        .with_for_update()
        .first()
    )
    if running is not None:
        stale_cutoff = datetime.now(timezone.utc) - STALE_RUN_THRESHOLD
        started_at = running.started_at
        # Postgres returns tz-aware datetimes for DateTime(timezone=True)
        # columns; SQLite (e.g. the test suite) always returns naive ones
        # regardless of column type. Normalize so the comparison below never
        # depends on which DB backend happens to be connected.
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        if started_at >= stale_cutoff:
            raise HTTPException(status_code=409, detail="Ingestion is already running")
        # Orphaned by a worker restart/crash mid-task — mark it failed so it
        # stops blocking new runs, then fall through to queue a fresh one.
        running.status = "failure"
        running.error = "Marked as stale after exceeding the run timeout (worker likely restarted mid-task)"
        running.finished_at = datetime.now(timezone.utc)
        db.commit()

    async_result = run_ingestion_task.delay(trigger="manual")
    return {"message": "Ingestion queued", "task_id": async_result.id}
