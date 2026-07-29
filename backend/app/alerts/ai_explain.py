"""
Optional AI explanation for breaking changes. Fully optional: if no
OPENAI_API_KEY is set, this is skipped entirely and the rest of the product
works exactly the same — the diff engine's own message is always sufficient
on its own.
"""
from openai import OpenAI

from app.core.config import settings


def explain_breaking_change(monitor_name: str, changes: list[dict]) -> str | None:
    if not settings.openai_api_key:
        return None

    critical_changes = [c["message"] for c in changes if c["severity"] == "critical"]
    if not critical_changes:
        return None

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = (
        f"A contract monitoring tool detected breaking changes in '{monitor_name}':\n"
        + "\n".join(f"- {c}" for c in critical_changes)
        + "\n\nIn under 80 words, explain why this matters to API/tool consumers and "
        "recommend one concrete action. Be direct and concrete, no fluff."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return response.choices[0].message.content
    except Exception:
        return None  # AI explanation is a nice-to-have, never block the alert on it
