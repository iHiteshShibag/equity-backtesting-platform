from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/backtesting_db"
    CORS_ORIGINS: str = "http://localhost:5173"

    # SQLAlchemy connection pool. Kept modest by default since Postgres itself
    # only allows ~100 connections; when running multiple backend/worker
    # replicas behind PgBouncer, PgBouncer -- not these values -- is what
    # keeps total server-side connections bounded.
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE_SECONDS: int = 1800

    # Auth
    SECRET_KEY: str = "replace_with_a_long_random_value"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Bootstrap admin account, used only by scripts/seed_admin.py
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "change_me"

    # Celery / Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Observability
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: str = ""

    # Email (rebalance-alert notifications for saved strategies). Left blank
    # in development -- app/core/email.py logs a warning and skips sending
    # rather than failing when these aren't configured.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "alerts@equity-backtesting.local"

    class Config:
        env_file = ".env"

settings = Settings()
