from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, ForeignKey, UniqueConstraint, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Stock(Base):
    __tablename__ = "stocks"
    id       = Column(Integer, primary_key=True, autoincrement=True)
    ticker   = Column(String(20), nullable=False, unique=True)
    name     = Column(String(200), nullable=False, default="")
    exchange = Column(String(10), nullable=False, default="NSE")
    sector   = Column(String(100))
    industry = Column(String(100))
    prices   = relationship("DailyPrice", back_populates="stock", cascade="all, delete-orphan")
    funds    = relationship("Fundamental", back_populates="stock", cascade="all, delete-orphan")


class DailyPrice(Base):
    __tablename__ = "daily_prices"
    id        = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id  = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date      = Column(Date, nullable=False)
    open      = Column(Numeric(14, 4))
    high      = Column(Numeric(14, 4))
    low       = Column(Numeric(14, 4))
    close     = Column(Numeric(14, 4), nullable=False)
    adj_close = Column(Numeric(14, 4))
    volume    = Column(BigInteger)
    stock     = relationship("Stock", back_populates="prices")
    __table_args__ = (UniqueConstraint("stock_id", "date", name="uq_price_stock_date"),)


class Fundamental(Base):
    __tablename__ = "fundamentals"
    id               = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id         = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    report_date      = Column(Date, nullable=False)
    period_type      = Column(String(10), nullable=False, default="annual")
    fiscal_period    = Column(String(20))
    # P&L
    revenue          = Column(Numeric(18, 2))
    pat              = Column(Numeric(18, 2))
    eps              = Column(Numeric(10, 4))
    # Balance Sheet
    total_assets     = Column(Numeric(18, 2))
    total_equity     = Column(Numeric(18, 2))
    total_debt       = Column(Numeric(18, 2))
    capital_employed = Column(Numeric(18, 2))
    # Cash Flow
    cfo              = Column(Numeric(18, 2))
    # Ratios
    market_cap       = Column(Numeric(18, 2))
    pe_ratio         = Column(Numeric(10, 4))
    pb_ratio         = Column(Numeric(10, 4))
    roce             = Column(Numeric(10, 4))
    roe              = Column(Numeric(10, 4))
    debt_to_equity   = Column(Numeric(10, 4))
    stock            = relationship("Stock", back_populates="funds")
    __table_args__ = (UniqueConstraint("stock_id", "report_date", "period_type", name="uq_fund_stock_date_type"),)
