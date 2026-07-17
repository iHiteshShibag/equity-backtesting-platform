from app.core.config import settings


def test_database_url_is_configured():
    assert settings.DATABASE_URL
    assert settings.DATABASE_URL.startswith("postgresql://")


def test_cors_origins_is_configured():
    assert settings.CORS_ORIGINS
