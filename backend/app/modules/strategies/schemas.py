from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.modules.backtest.schemas import BacktestRequest


class SavedStrategyCreate(BaseModel):
    name: str
    request: BacktestRequest


class SavedStrategyOut(BaseModel):
    id: int
    name: str
    request: BacktestRequest
    rebalance_freq: Literal["monthly", "quarterly", "yearly"]
    next_rebalance_date: date
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SavedStrategyUpdate(BaseModel):
    is_active: bool
