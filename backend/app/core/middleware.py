"""
Request ID + access-log middleware. One request = one ID, attached to the
response header (`X-Request-ID`) and every log line emitted while handling
it — grep any request_id and you get the full trace across auth, the check
pipeline, and alert dispatch for that one call.
"""
import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.request_context import new_request_id, set_request_id
from app.core.metrics import http_requests_total, http_request_duration_seconds

logger = logging.getLogger("contractwatch.access")


def _route_template(request: Request) -> str:
    """
    Use the matched route's path template (e.g. '/monitors/{monitor_id}')
    rather than the raw path — avoids unbounded label cardinality in
    Prometheus from every distinct monitor ID showing up as its own path.
    """
    route = request.scope.get("route")
    return route.path if route is not None else request.url.path


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or new_request_id()
        set_request_id(request_id)

        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            # Unhandled exceptions are also logged by the global exception
            # handler in main.py — this line exists so the access log still
            # gets an entry (with timing) even when a request blows up.
            duration = time.monotonic() - start
            path = _route_template(request)
            http_requests_total.labels(method=request.method, path=path, status_code="500").inc()
            http_request_duration_seconds.labels(method=request.method, path=path).observe(duration)
            logger.error(
                "Request failed",
                extra={
                    "cw_request_id": request_id,
                    "cw_method": request.method,
                    "cw_path": request.url.path,
                    "cw_duration_ms": round(duration * 1000, 1),
                },
            )
            raise

        duration = time.monotonic() - start
        path = _route_template(request)
        http_requests_total.labels(method=request.method, path=path, status_code=str(response.status_code)).inc()
        http_request_duration_seconds.labels(method=request.method, path=path).observe(duration)

        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request handled",
            extra={
                "cw_request_id": request_id,
                "cw_method": request.method,
                "cw_path": request.url.path,
                "cw_status_code": response.status_code,
                "cw_duration_ms": round(duration * 1000, 1),
            },
        )
        return response
