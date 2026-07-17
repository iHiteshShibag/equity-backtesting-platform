from app.modules.auth.models import User


def test_list_users_requires_admin(make_user, make_client):
    member = make_user(email="member@example.com", role="member")
    client = make_client(member)

    response = client.get("/api/users")

    assert response.status_code == 403


def test_list_users_as_admin_returns_all_users(make_user, make_client):
    admin = make_user(email="admin@example.com", role="admin")
    make_user(email="other@example.com", role="member")
    client = make_client(admin)

    response = client.get("/api/users")

    assert response.status_code == 200
    emails = {u["email"] for u in response.json()}
    assert emails == {"admin@example.com", "other@example.com"}


def test_create_user_as_admin_succeeds(make_user, make_client):
    admin = make_user(role="admin")
    client = make_client(admin)

    response = client.post("/api/users", json={
        "email": "new@example.com", "password": "s3cret-pass", "full_name": "New", "role": "member",
    })

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == "member"


def test_create_user_as_member_is_forbidden(make_user, make_client):
    member = make_user(role="member")
    client = make_client(member)

    response = client.post("/api/users", json={
        "email": "new@example.com", "password": "s3cret-pass", "role": "member",
    })

    assert response.status_code == 403


def test_create_user_duplicate_email_conflicts(make_user, make_client):
    admin = make_user(role="admin")
    make_user(email="dup@example.com")
    client = make_client(admin)

    response = client.post("/api/users", json={
        "email": "dup@example.com", "password": "s3cret-pass", "role": "member",
    })

    assert response.status_code == 409


def test_create_user_invalid_role_rejected(make_user, make_client):
    admin = make_user(role="admin")
    client = make_client(admin)

    response = client.post("/api/users", json={
        "email": "x@example.com", "password": "s3cret-pass", "role": "superuser",
    })

    assert response.status_code == 400


def test_admin_can_change_another_users_role(make_user, make_client):
    admin = make_user(email="admin@example.com", role="admin")
    other = make_user(email="other@example.com", role="member")
    client = make_client(admin)

    response = client.patch(f"/api/users/{other.id}", json={"role": "admin"})

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_admin_cannot_demote_self(make_user, make_client):
    admin = make_user(role="admin")
    client = make_client(admin)

    response = client.patch(f"/api/users/{admin.id}", json={"role": "member"})

    assert response.status_code == 400


def test_admin_cannot_deactivate_self(make_user, make_client):
    admin = make_user(role="admin")
    client = make_client(admin)

    response = client.patch(f"/api/users/{admin.id}", json={"is_active": False})

    assert response.status_code == 400


def test_admin_can_deactivate_another_user(make_user, make_client):
    admin = make_user(email="admin@example.com", role="admin")
    other = make_user(email="other@example.com", role="member")
    client = make_client(admin)

    response = client.patch(f"/api/users/{other.id}", json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_update_nonexistent_user_returns_404(make_user, make_client):
    admin = make_user(role="admin")
    client = make_client(admin)

    response = client.patch("/api/users/99999", json={"role": "admin"})

    assert response.status_code == 404


def test_admin_cannot_delete_self(make_user, make_client):
    admin = make_user(role="admin")
    client = make_client(admin)

    response = client.delete(f"/api/users/{admin.id}")

    assert response.status_code == 400


def test_admin_can_delete_another_user(make_user, make_client, db_session):
    admin = make_user(email="admin@example.com", role="admin")
    other = make_user(email="other@example.com", role="member")
    client = make_client(admin)

    response = client.delete(f"/api/users/{other.id}")

    assert response.status_code == 204
    assert db_session.query(User).filter(User.id == other.id).first() is None


def test_delete_nonexistent_user_returns_404(make_user, make_client):
    admin = make_user(role="admin")
    client = make_client(admin)

    response = client.delete("/api/users/99999")

    assert response.status_code == 404
