from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, func

from app.db.base import Base
from app.modules.backtest.models import JSONType


class SavedStrategy(Base):
    __tablename__ = "saved_strategies"
    id                 = Column(Integer, primary_key=True, autoincrement=True)
    user_id            = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name               = Column(String(200), nullable=False)
    request            = Column(JSONType, nullable=False)
    rebalance_freq     = Column(String(20), nullable=False)
    next_rebalance_date = Column(Date, nullable=False)
    is_active          = Column(Boolean, nullable=False, server_default="true")
    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
