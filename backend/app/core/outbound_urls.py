"""Validation for user-controlled URLs the server fetches or posts to."""
import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeOutboundUrl(ValueError):
    """Raised when a URL could target an internal network address."""


def assert_safe_public_http_url(url: str) -> None:
    """Allow only public HTTP(S) endpoints after resolving every DNS address."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeOutboundUrl("URL must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise UnsafeOutboundUrl("URL credentials are not allowed")

    try:
        addresses = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise UnsafeOutboundUrl("URL host could not be resolved") from exc

    if not addresses:
        raise UnsafeOutboundUrl("URL host could not be resolved")
    for _, _, _, _, sockaddr in addresses:
        if not ipaddress.ip_address(sockaddr[0]).is_global:
            raise UnsafeOutboundUrl("Refusing to access a non-public network address")
