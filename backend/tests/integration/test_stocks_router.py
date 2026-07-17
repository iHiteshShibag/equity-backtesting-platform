def test_list_stocks_returns_empty_list_on_fresh_db(client):
    response = client.get("/api/stocks/list")
    assert response.status_code == 200
    assert response.json() == []


def test_get_unknown_stock_returns_404(client):
    response = client.get("/api/stocks/UNKNOWN.NS")
    assert response.status_code == 404
    assert response.json() == {"detail": "Stock not found"}


def test_backtest_health_check(client):
    response = client.get("/api/backtest/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
