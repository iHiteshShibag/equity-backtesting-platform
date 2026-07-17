import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.rate_limit import limiter
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.auth.deps import get_current_user
from app.modules.auth.models import User
from app.modules.auth.security import hash_password


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """The Limiter's storage is Redis (settings.REDIS_URL), shared with
    whatever's actually running in dev/prod -- without resetting it, a test
    that hits a rate-limited route (login, backtest/run) counts against the
    same budget as every other test run against this Redis instance, making
    the suite pass/fail depending on unrelated prior runs rather than its own
    logic."""
    limiter.reset()
    yield

# In-memory SQLite, not the configured DATABASE_URL — keeps the suite fast
# and independent of a running Postgres/Docker instance. StaticPool is
# required so every connection shares the same in-memory database instead
# of each getting its own empty one.
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """A SQLAlchemy session wrapped in a transaction that's rolled back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """A FastAPI TestClient with get_db/get_current_user overridden to use db_session
    and a fake authenticated user — the routes under test require auth, but the
    auth flow itself is exercised separately in tests/integration/test_auth_router.py.
    """

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return User(id=1, email="test@example.com", hashed_password="x", full_name="Test User")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session):
    """Factory fixture: create and persist a User row with sane defaults.
    Persisting (rather than a bare unsaved object) matters for tests where a
    route looks the user back up by id — e.g. admin self-demote/self-delete
    guards, or backtest-job ownership checks — since the id must be real."""

    def _make(email="user@example.com", role="member", is_active=True, full_name="Test User", tos_accepted=True):
        user = User(
            email=email,
            hashed_password=hash_password("irrelevant-for-these-tests"),
            full_name=full_name,
            role=role,
            is_active=is_active,
            tos_accepted_at=datetime.now(timezone.utc) if tos_accepted else None,
        )
        db_session.add(user)
        db_session.commit()
        return user

    return _make


@pytest.fixture
def make_client(db_session):
    """Factory fixture: a client authenticated as the given user. Lets a
    single test stand up multiple clients (e.g. two different users, or a
    member + an admin) to exercise cross-user authorization.

    app.dependency_overrides lives on the single shared `app` object, not on
    any individual TestClient — so if two clients from this factory just set
    the override once at creation time, whichever was created *last* would
    silently win for *both* clients' requests. Each returned client instead
    re-applies its own override immediately before every request.
    """

    def _make(user):
        def override_get_db():
            yield db_session

        def override_get_current_user():
            return user

        class ScopedClient:
            def _use_overrides(self):
                app.dependency_overrides[get_db] = override_get_db
                app.dependency_overrides[get_current_user] = override_get_current_user

            def __getattr__(self, name):
                def call(*args, **kwargs):
                    self._use_overrides()
                    return getattr(TestClient(app), name)(*args, **kwargs)
                return call

        return ScopedClient()

    yield _make
    app.dependency_overrides.clear()


@pytest.fixture
def patch_task_session(monkeypatch, db_session):
    """Celery tasks open their own `SessionLocal()` bound to the real
    DATABASE_URL — there's no FastAPI dependency-injection point to override
    there. This redirects a given task module's SessionLocal to this test's
    db_session, so task-body unit tests can run against the same in-memory
    DB without a real Postgres connection.

    The task always closes its session in a `finally` block; since db_session
    is shared with the test itself (for assertions afterward), closing is
    patched to a no-op rather than actually severing it.
    """
    monkeypatch.setattr(db_session, "close", lambda: None)

    def _patch(module):
        monkeypatch.setattr(module, "SessionLocal", lambda: db_session)

    return _patch
