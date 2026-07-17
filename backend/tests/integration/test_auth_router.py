import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.modules.auth.models import User
from app.modules.auth.security import create_access_token, hash_password


@pytest.fixture
def auth_client(db_session):
    """A TestClient with only get_db overridden — get_current_user runs for real,
    so login/refresh/protected-route behavior is exercised end-to-end."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _create_user(db_session, email="user@example.com", password="s3cret-pass"):
    user = User(email=email, hashed_password=hash_password(password), full_name="Test User")
    db_session.add(user)
    db_session.commit()
    return user


def test_login_with_correct_password_returns_tokens(db_session, auth_client):
    _create_user(db_session)

    response = auth_client.post("/api/auth/login", json={"email": "user@example.com", "password": "s3cret-pass"})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert "refresh_token" not in body
    # Refresh token is httpOnly -- present as a cookie, never in the JSON body.
    assert "refresh_token" in response.cookies


def test_login_with_wrong_password_is_rejected(db_session, auth_client):
    _create_user(db_session)

    response = auth_client.post("/api/auth/login", json={"email": "user@example.com", "password": "wrong"})

    assert response.status_code == 401


def test_protected_route_without_token_is_rejected(auth_client):
    response = auth_client.get("/api/stocks/list")

    assert response.status_code == 401


def test_refresh_token_issues_new_access_token(db_session, auth_client):
    _create_user(db_session)

    auth_client.post("/api/auth/login", json={"email": "user@example.com", "password": "s3cret-pass"})

    # No body needed -- the refresh token travels as the httpOnly cookie the
    # TestClient's jar already picked up from the login response.
    refresh_res = auth_client.post("/api/auth/refresh")

    assert refresh_res.status_code == 200
    assert refresh_res.json()["access_token"]


def test_refresh_without_cookie_is_rejected(auth_client):
    response = auth_client.post("/api/auth/refresh")

    assert response.status_code == 401


def test_logout_clears_refresh_cookie(db_session, auth_client):
    _create_user(db_session)
    auth_client.post("/api/auth/login", json={"email": "user@example.com", "password": "s3cret-pass"})

    logout_res = auth_client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    refresh_res = auth_client.post("/api/auth/refresh")
    assert refresh_res.status_code == 401


def test_protected_route_with_valid_access_token_succeeds(db_session, auth_client):
    _create_user(db_session)

    login_res = auth_client.post("/api/auth/login", json={"email": "user@example.com", "password": "s3cret-pass"})
    access_token = login_res.json()["access_token"]

    response = auth_client.get("/api/stocks/list", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200


def test_me_reports_tos_not_yet_accepted_for_new_user(db_session, auth_client):
    user = _create_user(db_session)
    # Mints a token directly rather than going through /api/auth/login, which
    # is rate-limited to 5/minute -- a budget the other tests in this module
    # already spend, and re-testing that limit isn't this test's concern.
    headers = {"Authorization": f"Bearer {create_access_token(user.email)}"}

    response = auth_client.get("/api/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["tos_accepted_at"] is None


def test_accept_tos_sets_timestamp_and_is_reflected_in_me(db_session, auth_client):
    user = _create_user(db_session)
    headers = {"Authorization": f"Bearer {create_access_token(user.email)}"}

    accept_res = auth_client.post("/api/auth/accept-tos", headers=headers)
    assert accept_res.status_code == 200
    assert accept_res.json()["tos_accepted_at"] is not None

    me_res = auth_client.get("/api/auth/me", headers=headers)
    assert me_res.json()["tos_accepted_at"] is not None
