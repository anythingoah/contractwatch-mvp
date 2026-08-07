"""Inbound request-size and cookie-CSRF protections."""
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings


class RequestBodyLimitMiddleware:
    """Reject oversized bodies, including chunked requests without Content-Length."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        content_length = dict(scope.get("headers", [])).get(b"content-length")
        if content_length is not None:
            try:
                if int(content_length) > settings.max_request_body_bytes:
                    await self._send_too_large(scope, send)
                    return
            except ValueError:
                await self._send_too_large(scope, send)
                return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > settings.max_request_body_bytes:
                    raise HTTPException(status_code=413, detail="Request body too large")
            return message

        await self.app(scope, limited_receive, send)

    @staticmethod
    async def _send_too_large(scope, send) -> None:
        await JSONResponse(status_code=413, content={"detail": "Request body too large"})(scope, receive=None, send=send)


class CookieOriginProtectionMiddleware:
    """Reject cross-origin unsafe requests authenticated with the session cookie."""

    UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or scope["method"] not in self.UNSAFE_METHODS:
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        origin = request.headers.get("origin")
        if request.cookies.get(settings.cookie_name) and origin and origin not in settings.cors_origin_list:
            await JSONResponse(status_code=403, content={"detail": "Cross-origin request rejected"})(scope, receive, send)
            return
        await self.app(scope, receive, send)
