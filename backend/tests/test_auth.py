"""
Auth flow tests: signup, duplicate email rejection, login success/failure,
cookie-based session, logout, and the /auth/me identity check.
"""


def test_signup_sets_auth_cookie_and_returns_user(client):
    resp = client.post("/auth/signup", json={"email": "a@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "a@example.com"
    assert "cw_token" in resp.cookies


def test_signup_duplicate_email_rejected(client):
    client.post("/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    resp = client.post("/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    assert resp.status_code == 400


def test_signup_short_password_rejected(client):
    resp = client.post("/auth/signup", json={"email": "b@example.com", "password": "short"})
    assert resp.status_code == 422


def test_login_success(client):
    client.post("/auth/signup", json={"email": "c@example.com", "password": "password123"})
    resp = client.post("/auth/login", json={"email": "c@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "cw_token" in resp.cookies


def test_login_wrong_password_rejected(client):
    client.post("/auth/signup", json={"email": "d@example.com", "password": "password123"})
    resp = client.post("/auth/login", json={"email": "d@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email_rejected(client):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user_when_authenticated(auth_client):
    resp = auth_client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


def test_logout_clears_session(auth_client):
    assert auth_client.get("/auth/me").status_code == 200
    auth_client.post("/auth/logout")
    assert auth_client.get("/auth/me").status_code == 401
