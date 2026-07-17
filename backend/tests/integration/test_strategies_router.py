VALID_REQUEST = {"start_date": "2020-01-01", "end_date": "2021-01-01"}


def test_save_strategy_computes_next_rebalance_date(make_user, make_client):
    user = make_user()
    client = make_client(user)

    response = client.post(
        "/api/strategies/", json={"name": "My Strategy", "request": VALID_REQUEST}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "My Strategy"
    assert body["rebalance_freq"] == "quarterly"
    assert body["is_active"] is True
    assert body["next_rebalance_date"]


def test_save_strategy_rejected_without_tos_acceptance(make_user, make_client):
    user = make_user(tos_accepted=False)
    client = make_client(user)

    response = client.post(
        "/api/strategies/", json={"name": "My Strategy", "request": VALID_REQUEST}
    )

    assert response.status_code == 403


def test_list_strategies_only_returns_own(make_user, make_client):
    user_a = make_user(email="a@example.com")
    user_b = make_user(email="b@example.com")
    client_a = make_client(user_a)
    client_b = make_client(user_b)

    client_a.post("/api/strategies/", json={"name": "A's strategy", "request": VALID_REQUEST})
    client_b.post("/api/strategies/", json={"name": "B's strategy", "request": VALID_REQUEST})

    response = client_a.get("/api/strategies/")

    assert response.status_code == 200
    names = [s["name"] for s in response.json()]
    assert names == ["A's strategy"]


def test_update_strategy_toggles_active_flag(make_user, make_client):
    user = make_user()
    client = make_client(user)
    strategy_id = client.post(
        "/api/strategies/", json={"name": "S1", "request": VALID_REQUEST}
    ).json()["id"]

    response = client.patch(f"/api/strategies/{strategy_id}", json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_update_other_users_strategy_is_hidden(make_user, make_client):
    owner = make_user(email="owner@example.com")
    other = make_user(email="other@example.com")
    owner_client = make_client(owner)
    other_client = make_client(other)
    strategy_id = owner_client.post(
        "/api/strategies/", json={"name": "S1", "request": VALID_REQUEST}
    ).json()["id"]

    response = other_client.patch(f"/api/strategies/{strategy_id}", json={"is_active": False})

    assert response.status_code == 404


def test_delete_strategy_removes_it_from_list(make_user, make_client):
    user = make_user()
    client = make_client(user)
    strategy_id = client.post(
        "/api/strategies/", json={"name": "S1", "request": VALID_REQUEST}
    ).json()["id"]

    delete_response = client.delete(f"/api/strategies/{strategy_id}")
    assert delete_response.status_code == 204

    list_response = client.get("/api/strategies/")
    assert list_response.json() == []
