"""
Email sending, kept behind one function so the provider (Resend vs SendGrid)
is swappable without touching call sites. Defaults to Resend's API.
"""
import httpx

from app.core.config import settings


def send_email_alert(to_email: str, monitor_name: str, changes: list[dict]) -> bool:
    if not settings.email_api_key:
        return False  # no provider configured — fail soft, don't crash the check

    critical = [c for c in changes if c["severity"] == "critical"]
    subject = f"{'🚨 Breaking change' if critical else 'Contract change'} detected: {monitor_name}"

    change_lines = "\n".join(f"- [{c['severity']}] {c['message']}" for c in changes[:10])
    body_text = f"ContractWatch detected {len(changes)} change(s) in {monitor_name}:\n\n{change_lines}"

    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.email_api_key}"},
            json={
                "from": settings.email_from,
                "to": [to_email],
                "subject": subject,
                "text": body_text,
            },
            timeout=10.0,
        )
        return resp.status_code < 300
    except httpx.HTTPError:
        return False
