import socket

import pytest

from app.core.outbound_urls import UnsafeOutboundUrl, assert_safe_public_http_url


def test_request_body_limit_rejects_oversized_payload(client):
    response = client.post(
        "/auth/login",
        content=b"x" * (16 * 1024 * 1024 + 1),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413


def test_cookie_authenticated_cross_origin_post_is_rejected(auth_client):
    response = auth_client.post("/auth/logout", headers={"origin": "https://attacker.example"})
    assert response.status_code == 403


def test_outbound_url_rejects_private_literal():
    with pytest.raises(UnsafeOutboundUrl):
        assert_safe_public_http_url("http://127.0.0.1:8000/openapi.json")


def test_outbound_url_rejects_hostname_resolving_to_private_ip(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.10", 443))],
    )
    with pytest.raises(UnsafeOutboundUrl):
        assert_safe_public_http_url("https://internal.example/openapi.json")
