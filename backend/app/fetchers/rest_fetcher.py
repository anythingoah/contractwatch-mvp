"""
Fetches and parses an OpenAPI spec (JSON or YAML) from a URL.
"""
import json
import ipaddress
from urllib.parse import urljoin, urlparse

import httpx
import yaml

from app.fetchers.retry import with_transient_retry
from app.core.outbound_urls import UnsafeOutboundUrl, assert_safe_public_http_url


class FetchError(Exception):
    pass


def _get_with_safe_redirects(url: str, timeout: float) -> httpx.Response:
    """Fetch while checking the initial target and every redirect target."""
    current_url = url
    for _ in range(4):
        try:
            assert_safe_public_http_url(current_url)
        except UnsafeOutboundUrl as exc:
            raise FetchError(str(exc)) from exc
        response = httpx.get(current_url, timeout=timeout, follow_redirects=False)
        if response.is_redirect:
            location = response.headers.get("location")
            if not location:
                raise FetchError("Redirect response did not include a location")
            current_url = urljoin(current_url, location)
            continue
        response.raise_for_status()
        return response
    raise FetchError("Too many redirects while fetching OpenAPI spec")


def _reject_private_targets(url: str) -> None:
    """
    Basic SSRF guard: refuse to fetch private/link-local IP literals.
    Not exhaustive (doesn't resolve DNS), but blocks the obvious cases —
    good enough for MVP, revisit if abuse shows up.
    """
    host = urlparse(url).hostname or ""
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise FetchError("Refusing to fetch private/internal address")
    except ValueError:
        pass  # not a literal IP, fine — DNS resolution check is a future improvement


def fetch_openapi_spec(spec_url: str, timeout: float = 15.0) -> dict:
    """Fetch an OpenAPI spec from a URL and parse it as JSON or YAML."""
    _reject_private_targets(spec_url)

    @with_transient_retry
    def _get() -> httpx.Response:
        return _get_with_safe_redirects(spec_url, timeout)

    try:
        resp = _get()
    except httpx.HTTPError as e:
        raise FetchError(f"Failed to fetch OpenAPI spec: {e}") from e

    text = resp.text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise FetchError(f"Spec is neither valid JSON nor YAML: {e}") from e
