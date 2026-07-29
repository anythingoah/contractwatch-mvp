"""
Centralized exception handling. Two things this buys us:
1. Every unhandled exception gets logged with full context (request_id,
   path, exception traceback) automatically — no route ever needs its own
   try/except just to log an error.
2. Every error response has one consistent shape:
   {"detail": "...", "request_id": "..."}
   — whether it came from a deliberate HTTPException (404, 402, 422, etc.)
   or an unexpected crash (500). Clients can always read `detail`.
"""
import json
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.request_context import get_request_id

logger = logging.getLogger("contractwatch.errors")


def _safe_validation_errors(errors):
    """Render Pydantic validation errors to JSON-safe dicts.

    Pydantic v2 may embed the original exception instance in the error `ctx`,
    which Python's stdlib json encoder cannot serialize. Convert any exception
    objects to their string representation.
    """
    def _default(obj):
        if isinstance(obj, BaseException):
            return str(obj)
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    return json.loads(json.dumps(errors, default=_default))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        # Deliberate, expected errors (404, 401, 402, 429, ...) — no need to
        # log at error level, FastAPI/Starlette already raised these on purpose.
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "request_id": get_request_id()},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": _safe_validation_errors(exc.errors()), "request_id": get_request_id()},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        # Anything that reaches here is a bug, not an expected error path.
        # Log the full traceback with request context; never leak internals
        # (stack traces, DB errors, etc.) into the response body.
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={
                "cw_request_id": get_request_id(),
                "cw_method": request.method,
                "cw_path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": get_request_id()},
        )
