"""
Adds baseline security headers to every response. This is an API (not a
page-serving app), so the CSP here is deliberately locked down — there's no
inline script/style to allow for.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    DOCS_PATHS = {"/docs", "/redoc", "/openapi.json"}

    DOCS_CSP = (
    "default-src 'none'; "
    "script-src https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
    "font-src https://fonts.gstatic.com; "
    "img-src https://fastapi.tiangolo.com data:; "
    "connect-src 'self'"
)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

        if request.url.path in self.DOCS_PATHS:
            response.headers["Content-Security-Policy"] = self.DOCS_CSP
        else:
            response.headers["Content-Security-Policy"] = "default-src 'none'"

        if settings.is_production and settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response