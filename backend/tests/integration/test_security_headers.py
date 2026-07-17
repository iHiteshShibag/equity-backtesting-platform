def test_api_response_includes_security_headers(client):
    resp = client.get("/health")

    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "strict-transport-security" in resp.headers
    assert resp.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"


def test_docs_page_is_not_locked_down_by_csp(client):
    resp = client.get("/docs")

    assert "content-security-policy" not in resp.headers
    # Other defensive headers still apply -- only the CSP is relaxed for docs.
    assert resp.headers["x-content-type-options"] == "nosniff"
