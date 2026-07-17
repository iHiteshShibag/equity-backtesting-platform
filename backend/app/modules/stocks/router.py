from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.modules.auth.deps import get_current_user
from app.modules.stocks.models import Stock
from app.db.session import get_db

router = APIRouter(prefix="/api/stocks", tags=["stocks"], dependencies=[Depends(get_current_user)])


@router.get("/list")
def list_stocks(
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get list of all available stocks."""
    stocks = db.query(Stock).order_by(Stock.ticker).offset(offset).limit(limit).all()
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
def get_stock(ticker: str, db: Session = Depends(get_db)):
    """Get stock details."""
    stock = db.query(Stock).filter(Stock.ticker == ticker).first()
    if not stock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")
    return {
        "ticker": stock.ticker,
        "name": stock.name,
        "exchange": stock.exchange,
        "sector": stock.sector,
    }
