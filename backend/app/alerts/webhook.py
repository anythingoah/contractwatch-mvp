"""Generic outbound webhook — POSTs a JSON payload describing the diff."""
import httpx

from app.core.outbound_urls import UnsafeOutboundUrl, assert_safe_public_http_url


def send_webhook_alert(webhook_url: str, monitor_name: str, severity: str, changes: list[dict]) -> bool:
    try:
        assert_safe_public_http_url(webhook_url)
    except UnsafeOutboundUrl:
        return False
    payload = {
        "monitor": monitor_name,
        "severity": severity,
        "changes": changes,
    }
    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10.0)
        return resp.status_code < 300
    except httpx.HTTPError:
        return False
