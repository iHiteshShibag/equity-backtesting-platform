from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import date


class RankMetric(BaseModel):
    metric: str
    order: Literal["asc", "desc"] = "desc"


class BacktestRequest(BaseModel):
    start_date: date
    end_date: date
    initial_capital: float = 1_000_000
    portfolio_size: int = 20
    rebalance_freq: Literal["monthly", "quarterly", "yearly"] = "quarterly"
    position_sizing: Literal["equal", "market_cap", "metric"] = "equal"
    sizing_metric: Optional[str] = None
    market_cap_min: Optional[float] = None
    market_cap_max: Optional[float] = None
    roce_min: Optional[float] = None
    pat_positive: bool = True
    rank_metrics: List[RankMetric] = []


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
    final_value: float


class BacktestResponse(BaseModel):
    timeseries: List[dict]
    rebalance_logs: List[dict]
    metrics: dict
    winners: List[dict] = []
    losers: List[dict] = []
