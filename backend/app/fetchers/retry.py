"""
Shared retry policy for outbound fetches. Retries only genuinely transient
failures (timeouts, connection errors, 5xx) — never 4xx, which means "this
URL/config is wrong" and retrying just burns time before reporting it.
"""
import logging

import httpx
from tenacity import (
    retry, retry_if_exception, stop_after_attempt, wait_exponential, before_sleep_log,
)

logger = logging.getLogger("contractwatch.fetchers")


def _is_transient(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


# 3 attempts, exponential backoff starting at 1s (1s, 2s, 4s) — bounded so a
# single scheduler tick can't hang indefinitely on one unreachable monitor.
with_transient_retry = retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
