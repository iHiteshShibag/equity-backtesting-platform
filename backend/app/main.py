from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import backtest_router, stocks_router
from app.database import engine, Base
from app.config import settings

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Equity Backtesting Platform",
    description="End-to-end backtesting platform for equity-based strategies",
    version="1.0.0",
)

# CORS middleware
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(backtest_router)
app.include_router(stocks_router)


@app.get("/")
async def root():
    return {
        "message": "Equity Backtesting Platform API",
        "docs": "/docs",
        "health": "/api/backtest/health",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
