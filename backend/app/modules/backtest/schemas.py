from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal
from datetime import date, datetime


class RankMetric(BaseModel):
    metric: str
    order: Literal["asc", "desc"] = "desc"


class BacktestRequest(BaseModel):
    start_date: date
    end_date: date
    initial_capital: float = Field(1_000_000, gt=0)
    # A non-positive portfolio_size would reach pandas' `.head(n)` in the
    # engine, where a negative n means "all but the last |n| rows" rather
    # than "empty" -- silently selecting far more stocks than intended.
    portfolio_size: int = Field(20, gt=0)
    rebalance_freq: Literal["monthly", "quarterly", "yearly"] = "quarterly"
    position_sizing: Literal["equal", "market_cap", "metric"] = "equal"
    sizing_metric: Optional[str] = None
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    roce_min: Optional[float] = None
    pat_positive: bool = True
    rank_metrics: List[RankMetric] = []
    commission_bps: float = 0
    slippage_pct: float = 0

    @model_validator(mode="after")
    def _check_date_range(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class UniverseCountOut(BaseModel):
    matched: int
    universe: int


class TimeseriesPoint(BaseModel):
    date: str
    portfolio_value: float
    drawdown: float = 0.0


class RebalanceLog(BaseModel):
    date: str
    portfolio_value: float
    holdings: list


class MetricsOut(BaseModel):
    cagr: float
    total_return: float
    sharpe: float
    sortino: float
    max_drawdown: float
    calmar: float
    win_rate: float
    final_value: float
    total_costs: float = 0


class BacktestResponse(BaseModel):
    timeseries: List[dict]
    rebalance_logs: List[dict]
    metrics: dict
    benchmark: Optional[dict] = None
    winners: List[dict] = []
    losers: List[dict] = []
    data_quality: Optional[dict] = None


class BacktestJobOut(BaseModel):
    id: int
    status: Literal["pending", "running", "success", "failure"]
    result: Optional[BacktestResponse] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
