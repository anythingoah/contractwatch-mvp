"""Send a formatted alert to a Slack Incoming Webhook URL."""
import httpx


def send_slack_alert(webhook_url: str, monitor_name: str, changes: list[dict]) -> bool:
    critical = [c for c in changes if c["severity"] == "critical"]
    header = "🚨 Contract Breaking Change" if critical else "⚠️ Contract Change Detected"

    lines = [f"*{header}*", f"*Monitor:* {monitor_name}", ""]
    for c in changes[:5]:  # cap so the message doesn't get huge
        emoji = "🔴" if c["severity"] == "critical" else ("🟡" if c["severity"] == "warning" else "ℹ️")
        lines.append(f"{emoji} {c['message']}")
    if len(changes) > 5:
        lines.append(f"...and {len(changes) - 5} more change(s)")

    payload = {"text": "\n".join(lines)}
    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10.0)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False
