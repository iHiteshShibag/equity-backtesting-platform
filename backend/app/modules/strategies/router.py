from datetime import date

import pandas as pd
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.ownership import get_owned_or_404
from app.db.session import get_db
from app.modules.auth.deps import require_tos_accepted
from app.modules.auth.models import User
from app.modules.strategies.models import SavedStrategy
from app.modules.strategies.schemas import SavedStrategyCreate, SavedStrategyOut, SavedStrategyUpdate

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

_FREQ_OFFSET = {
    "monthly": pd.DateOffset(months=1),
    "quarterly": pd.DateOffset(months=3),
    "yearly": pd.DateOffset(years=1),
}


def _next_rebalance_date(freq: str, after: date) -> date:
    return (pd.Timestamp(after) + _FREQ_OFFSET.get(freq, _FREQ_OFFSET["quarterly"])).date()


@router.post("/", response_model=SavedStrategyOut, status_code=status.HTTP_201_CREATED)
def save_strategy(
    body: SavedStrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tos_accepted),
):
    strategy = SavedStrategy(
        user_id=current_user.id,
        name=body.name,
        request=body.request.model_dump(mode="json"),
        rebalance_freq=body.request.rebalance_freq,
        next_rebalance_date=_next_rebalance_date(body.request.rebalance_freq, date.today()),
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


@router.get("/", response_model=list[SavedStrategyOut])
def list_strategies(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tos_accepted),
):
    return (
        db.query(SavedStrategy)
        .filter(SavedStrategy.user_id == current_user.id)
        .order_by(SavedStrategy.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.patch("/{strategy_id}", response_model=SavedStrategyOut)
def update_strategy(
    strategy_id: int,
    body: SavedStrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tos_accepted),
):
    strategy = get_owned_or_404(db, SavedStrategy, strategy_id, current_user, "Strategy not found")
    strategy.is_active = body.is_active
    db.commit()
    db.refresh(strategy)
    return strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tos_accepted),
):
    strategy = get_owned_or_404(db, SavedStrategy, strategy_id, current_user, "Strategy not found")
    db.delete(strategy)
    db.commit()
