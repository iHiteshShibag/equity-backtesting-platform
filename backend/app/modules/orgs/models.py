from sqlalchemy import Column, DateTime, Integer, String, func

from app.db.base import Base

VALID_TIERS = {"free", "pro", "enterprise"}

# Requests/minute per tier for the shared slowapi Limiter (app/core/rate_limit.py).
# Scaffolding only -- no billing/payment integration wires into `tier` yet,
# it's just a DB field an admin can set via PATCH /api/orgs/me.
TIER_RATE_LIMITS = {
    "free": "5/minute",
    "pro": "30/minute",
    "enterprise": "120/minute",
}


class Organization(Base):
    __tablename__ = "organizations"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(200), nullable=False)
    tier       = Column(String(20), nullable=False, server_default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
