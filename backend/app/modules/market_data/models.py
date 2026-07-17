from sqlalchemy import Column, Date, Integer, String, DateTime, Text, JSON, func
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base

# Generic JSON everywhere, JSONB specifically on Postgres — see the same
# pattern/rationale in app/modules/backtest/models.py.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id                    = Column(Integer, primary_key=True, autoincrement=True)
    trigger               = Column(String(20), nullable=False)
    status                = Column(String(20), nullable=False, server_default="running")
    step                  = Column(String(100), nullable=True)
    prices_success        = Column(Integer, nullable=False, server_default="0")
    prices_failed         = Column(Integer, nullable=False, server_default="0")
    prices_failed_tickers = Column(JSONType, nullable=True)
    funds_success         = Column(Integer, nullable=False, server_default="0")
    funds_failed          = Column(Integer, nullable=False, server_default="0")
    funds_failed_tickers  = Column(JSONType, nullable=True)
    error                 = Column(Text, nullable=True)
    started_at            = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at           = Column(DateTime(timezone=True), nullable=True)


class IndexMembership(Base):
    """Point-in-time index constituency. A null end_date means the ticker is
    still a member. Manually maintained -- see index_membership_seed.py for
    provenance/caveats -- not sourced from a licensed index-history feed."""
    __tablename__ = "index_memberships"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    index_name = Column(String(50), nullable=False, server_default="NIFTY100")
    ticker     = Column(String(20), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date   = Column(Date, nullable=True)
