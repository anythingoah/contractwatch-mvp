"""Generic outbound webhook — POSTs a JSON payload describing the diff."""
import httpx


def send_webhook_alert(webhook_url: str, monitor_name: str, severity: str, changes: list[dict]) -> bool:
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
