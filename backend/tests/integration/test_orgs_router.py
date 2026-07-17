from app.modules.orgs.models import Organization


def _make_org(db_session, name="Acme", tier="free"):
    org = Organization(name=name, tier=tier)
    db_session.add(org)
    db_session.commit()
    return org


def test_get_my_org_returns_404_when_unassigned(make_user, make_client):
    user = make_user()
    client = make_client(user)

    response = client.get("/api/orgs/me")

    assert response.status_code == 404


def test_get_my_org_returns_assigned_org(db_session, make_user, make_client):
    org = _make_org(db_session)
    user = make_user()
    user.org_id = org.id
    db_session.commit()
    client = make_client(user)

    response = client.get("/api/orgs/me")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Acme"
    assert body["tier"] == "free"


def test_update_my_org_requires_admin(db_session, make_user, make_client):
    org = _make_org(db_session)
    member = make_user(role="member")
    member.org_id = org.id
    db_session.commit()
    client = make_client(member)

    response = client.patch("/api/orgs/me", json={"tier": "pro"})

    assert response.status_code == 403


def test_update_my_org_as_admin_changes_tier(db_session, make_user, make_client):
    org = _make_org(db_session)
    admin = make_user(role="admin")
    admin.org_id = org.id
    db_session.commit()
    client = make_client(admin)

    response = client.patch("/api/orgs/me", json={"tier": "pro"})

    assert response.status_code == 200
    assert response.json()["tier"] == "pro"


def test_update_my_org_rejects_invalid_tier(db_session, make_user, make_client):
    org = _make_org(db_session)
    admin = make_user(role="admin")
    admin.org_id = org.id
    db_session.commit()
    client = make_client(admin)

    response = client.patch("/api/orgs/me", json={"tier": "unlimited"})

    assert response.status_code == 400
