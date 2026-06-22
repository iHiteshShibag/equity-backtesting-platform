from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import traceback

from app.schemas.backtest import BacktestRequest, BacktestResponse
from app.engine.backtest_engine import BacktestEngine, BacktestConfig
from app.database import get_db

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(req: BacktestRequest, db: Session = Depends(get_db)):
    """Run a backtest with given parameters."""
    try:
        cfg = BacktestConfig(
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.initial_capital,
            portfolio_size=req.portfolio_size,
            rebalance_freq=req.rebalance_freq,
            position_sizing=req.position_sizing,
            sizing_metric=req.sizing_metric,
            market_cap_min=req.market_cap_min,
            market_cap_max=req.market_cap_max,
            roce_min=req.roce_min,
            pat_positive=req.pat_positive,
            rank_metrics=req.rank_metrics,
        )

        engine = BacktestEngine(cfg, db)
        result = engine.run()

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return BacktestResponse(
            timeseries=result.get("timeseries", []),
            rebalance_logs=result.get("rebalance_logs", []),
            metrics=result.get("metrics", {}),
            winners=result.get("winners", []),
            losers=result.get("losers", []),
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Backtest failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
