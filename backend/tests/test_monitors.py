"""
Monitor CRUD, validation, plan-limit enforcement, and ownership isolation.
"""

REST_PAYLOAD = {
    "name": "Stripe API",
    "type": "rest",
    "frequency": "daily",
    "openapi_spec_url": "https://api.example.com/openapi.json",
    "channels": [],
}

MCP_PAYLOAD = {
    "name": "GitHub MCP",
    "type": "mcp",
    "frequency": "daily",
    "mcp_server_url": "https://mcp.example.com",
    "channels": [],
}


def test_create_rest_monitor(auth_client):
    resp = auth_client.post("/monitors", json=REST_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Stripe API"
    assert body["status"] == "pending"


def test_create_mcp_monitor(auth_client):
    resp = auth_client.post("/monitors", json=MCP_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json()["type"] == "mcp"


def test_rest_monitor_requires_openapi_spec_url(auth_client):
    payload = {**REST_PAYLOAD, "openapi_spec_url": None}
    resp = auth_client.post("/monitors", json=payload)
    assert resp.status_code == 422


def test_mcp_monitor_requires_server_url(auth_client):
    payload = {**MCP_PAYLOAD, "mcp_server_url": None}
    resp = auth_client.post("/monitors", json=payload)
    assert resp.status_code == 422


def test_invalid_url_rejected(auth_client):
    payload = {**REST_PAYLOAD, "openapi_spec_url": "not-a-url"}
    resp = auth_client.post("/monitors", json=payload)
    assert resp.status_code == 422


def test_invalid_frequency_rejected(auth_client):
    payload = {**REST_PAYLOAD, "frequency": "every_5_seconds"}
    resp = auth_client.post("/monitors", json=payload)
    assert resp.status_code == 422


def test_slack_channel_requires_webhook_url(auth_client):
    payload = {**REST_PAYLOAD, "channels": [{"type": "slack", "configuration": {}}]}
    resp = auth_client.post("/monitors", json=payload)
    assert resp.status_code == 422


def test_email_channel_requires_valid_email(auth_client):
    payload = {**REST_PAYLOAD, "channels": [{"type": "email", "configuration": {"email": "not-an-email"}}]}
    resp = auth_client.post("/monitors", json=payload)
    assert resp.status_code == 422


def test_free_plan_monitor_limit_enforced(auth_client):
    # Free plan default limit is 2 (see settings.free_plan_monitor_limit)
    auth_client.post("/monitors", json=REST_PAYLOAD)
    auth_client.post("/monitors", json={**REST_PAYLOAD, "name": "Second"})
    resp = auth_client.post("/monitors", json={**REST_PAYLOAD, "name": "Third"})
    assert resp.status_code == 402


def test_free_plan_cannot_use_hourly_frequency(auth_client):
    resp = auth_client.post("/monitors", json={**REST_PAYLOAD, "frequency": "hourly"})
    assert resp.status_code == 402


def test_list_monitors_requires_auth(client):
    resp = client.get("/monitors")
    assert resp.status_code == 401


def test_users_cannot_see_each_others_monitors(client):
    client.post("/auth/signup", json={"email": "owner@example.com", "password": "password123"})
    created = client.post("/monitors", json=REST_PAYLOAD).json()

    client.post("/auth/logout")
    client.post("/auth/signup", json={"email": "other@example.com", "password": "password123"})

    resp = client.get(f"/monitors/{created['id']}")
    assert resp.status_code == 404


def test_delete_monitor(auth_client):
    created = auth_client.post("/monitors", json=REST_PAYLOAD).json()
    resp = auth_client.delete(f"/monitors/{created['id']}")
    assert resp.status_code == 204
    assert auth_client.get(f"/monitors/{created['id']}").status_code == 404
