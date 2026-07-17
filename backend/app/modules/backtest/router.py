import logging
from datetime import datetime, date
from types import SimpleNamespace

import pandas as pd
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.cache import cached
from app.core.ownership import get_owned_or_404
from app.core.rate_limit import limiter, org_tier_rate_limit
from app.modules.auth.deps import get_current_user, require_tos_accepted
from app.modules.auth.models import User
from app.modules.backtest.schemas import BacktestRequest, BacktestJobOut, UniverseCountOut
from app.modules.backtest.models import BacktestJob
from app.modules.backtest.tasks import run_backtest_task
from app.modules.backtest.engine.filters import apply_filters
from app.modules.market_data.index_membership import get_active_tickers
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# Latest annual fundamentals per ticker via a portable window function
# (works on both Postgres and the SQLite test DB, unlike Postgres-only
# DISTINCT ON) instead of pulling every historical row and reducing it in
# pandas -- this endpoint only ever needs "as of today", not the full history.
_LATEST_FUNDAMENTALS_SQL = text("""
    SELECT ticker, report_date, market_cap, roce, pat FROM (
        SELECT s.ticker, f.report_date, f.market_cap, f.roce, f.pat,
               ROW_NUMBER() OVER (PARTITION BY s.ticker ORDER BY f.report_date DESC) AS rn
        FROM fundamentals f
        JOIN stocks s ON s.id = f.stock_id
        WHERE f.period_type = 'annual'
    ) latest
    WHERE rn = 1
""")


@router.post("/run", response_model=BacktestJobOut, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(org_tier_rate_limit)
def run_backtest(
    request: Request,
    req: BacktestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tos_accepted),
):
    """Queue a backtest job and return immediately; poll /jobs/{id} for the result."""
    job = BacktestJob(
        user_id=current_user.id,
        status="pending",
        request=req.model_dump(mode="json"),
    )
    db.add(job)
    db.commit()

    run_backtest_task.delay(job.id)

    return job


@router.get("/jobs/{job_id}", response_model=BacktestJobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_owned_or_404(db, BacktestJob, job_id, current_user, "Job not found")


@router.get("/jobs", response_model=list[BacktestJobOut])
def list_jobs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(BacktestJob)
        .filter(BacktestJob.user_id == current_user.id)
        .order_by(BacktestJob.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def _universe_count_cache_key(*args, **kwargs) -> str:
    # Fundamentals only change once a day (the scheduled ingestion run), so
    # folding today's date into the key -- rather than an explicit
    # invalidation hook -- is enough to bound staleness to "at most a day".
    return (
        f"{kwargs.get('market_cap_min')}:{kwargs.get('market_cap_max')}:"
        f"{kwargs.get('roce_min')}:{kwargs.get('pat_positive')}:{date.today()}"
    )


@router.get("/universe-count", response_model=UniverseCountOut)
@cached("universe-count", ttl_seconds=300, key_fn=_universe_count_cache_key)
def universe_count(
    market_cap_min: float | None = Query(None),
    market_cap_max: float | None = Query(None),
    roce_min: float | None = Query(None),
    pat_positive: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Count NIFTY100 stocks whose latest annual fundamentals pass the given
    filters, as of today. For config-screen preview only -- reuses the same
    apply_filters() the engine runs per-rebalance, but against today's latest
    fundamentals rather than a historical point-in-time snapshot, so this is
    an approximation of what a backtest starting today would select from."""
    try:
        df = pd.read_sql(_LATEST_FUNDAMENTALS_SQL, db.bind)
    except Exception:
        logger.exception("Failed loading fundamentals for universe-count")
        return {"matched": 0, "universe": 0}

    if df.empty:
        return {"matched": 0, "universe": 0}

    active_tickers = get_active_tickers(db, "NIFTY100", date.today())
    if active_tickers:
        df = df[df["ticker"].isin(active_tickers)]

    universe_size = len(df)

    cfg = SimpleNamespace(
        market_cap_min=market_cap_min,
        market_cap_max=market_cap_max,
        roce_min=roce_min,
        pat_positive=pat_positive,
    )
    matched = len(apply_filters(df, cfg))

    return {"matched": matched, "universe": universe_size}


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
