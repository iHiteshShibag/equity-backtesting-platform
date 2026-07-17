from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    email           = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(200), nullable=True)
    role            = Column(String(20), nullable=False, server_default="member")
    is_active       = Column(Boolean, nullable=False, server_default="true")
    tos_accepted_at = Column(DateTime(timezone=True), nullable=True)
    org_id          = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org = relationship("Organization", lazy="joined")
