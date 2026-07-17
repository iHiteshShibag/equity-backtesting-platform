from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base

# Generic JSON everywhere, JSONB specifically on Postgres — keeps the ORM
# model usable against SQLite (e.g. the test suite) while still getting
# efficient indexed JSON storage in production.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class BacktestJob(Base):
    __tablename__ = "backtest_jobs"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status       = Column(String(20), nullable=False, server_default="pending")
    request      = Column(JSONType, nullable=False)
    result       = Column(JSONType, nullable=True)
    error        = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
