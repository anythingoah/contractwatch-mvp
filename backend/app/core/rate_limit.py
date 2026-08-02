"""
Minimal in-memory rate limiter for auth endpoints (signup/login). No Redis
dependency — a plain dict guarded by a lock is enough for a single-process
MVP deployment, which is the same assumption the scheduler already makes
(see scheduler/jobs.py). If you split into multiple API replicas, this
needs to move to Redis at the same time the scheduler does — a shared-state
problem either way.
"""
import time
import threading
from collections import defaultdict

from fastapi import HTTPException, Request, status

from app.core.config import settings

_lock = threading.Lock()
_hits: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    # Respect a reverse proxy's forwarded header if present (Cloudflare, etc.)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency: raises 429 if this IP has exceeded the auth rate limit."""
    key = _client_ip(request)
    now = time.monotonic()
    window_start = now - settings.auth_rate_limit_window_seconds

    with _lock:
        # Drop stale IPs so the in-memory map cannot grow without bound.
        stale_keys = [k for k, hits in _hits.items() if not hits or hits[-1] <= window_start]
        for stale_key in stale_keys:
            del _hits[stale_key]

        recent = [t for t in _hits[key] if t > window_start]
        if len(recent) >= settings.auth_rate_limit_requests:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Too many attempts. Please wait a moment before trying again.",
            )
        recent.append(now)
        _hits[key] = recent


def reset_rate_limit() -> None:
    """Clear all rate-limit state. Useful in tests so one test's requests don't
    cause 429s for the next test (they all share the same client IP).
    """
    with _lock:
        _hits.clear()
