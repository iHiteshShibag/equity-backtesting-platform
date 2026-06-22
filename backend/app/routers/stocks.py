from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.stock import Stock
from app.database import get_db

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/list")
async def list_stocks(db: Session = Depends(get_db)):
    """Get list of all available stocks."""
    stocks = db.query(Stock).all()
    return [
        {
            "ticker": s.ticker,
            "name": s.name,
            "exchange": s.exchange,
            "sector": s.sector,
        }
        for s in stocks
    ]


@router.get("/{ticker}")
async def get_stock(ticker: str, db: Session = Depends(get_db)):
    """Get stock details."""
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if not stock:
        return {"error": "Stock not found"}
    return {
        "ticker": stock.ticker,
        "name": stock.name,
        "exchange": stock.exchange,
        "sector": stock.sector,
    }
