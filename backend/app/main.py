import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.observability import setup_logging, setup_sentry
from app.core.rate_limit import limiter
from app.modules.auth.router import router as auth_router
from app.modules.backtest.router import router as backtest_router
from app.modules.stocks.router import router as stocks_router
from app.modules.market_data.router import router as market_data_router
from app.modules.users.router import router as users_router
from app.modules.strategies.router import router as strategies_router
from app.modules.orgs.router import router as orgs_router

setup_logging()
setup_sentry()

logger = logging.getLogger(__name__)

_INSECURE_DEFAULTS = {
    "SECRET_KEY": "replace_with_a_long_random_value",
    "ADMIN_PASSWORD": "change_me",
}


def _assert_production_secrets_configured() -> None:
    """Refuse to boot in production with a default SECRET_KEY/ADMIN_PASSWORD
    still in place -- a misconfigured prod deploy would otherwise silently
    run with a publicly known JWT signing key or admin credential."""
    if settings.ENVIRONMENT != "production":
        return
    offenders = [
        name for name, default in _INSECURE_DEFAULTS.items()
        if getattr(settings, name) == default
    ]
    if offenders:
        raise RuntimeError(
            f"Refusing to start in production with default value(s) for: {', '.join(offenders)}. "
            "Set them via environment variables/.env before deploying."
        )


_assert_production_secrets_configured()

app = FastAPI(
    title="Equity Backtesting Platform",
    description="End-to-end backtesting platform for equity-based strategies",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception", extra={"path": request.url.path, "method": request.method}
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# CORS middleware
origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else []
if settings.ENVIRONMENT == "production" and not origins:
    raise RuntimeError("CORS_ORIGINS must be set explicitly in production (no localhost fallback).")
if not origins:
    origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(backtest_router)
app.include_router(stocks_router)
app.include_router(market_data_router)
app.include_router(users_router)
app.include_router(strategies_router)
app.include_router(orgs_router)


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
