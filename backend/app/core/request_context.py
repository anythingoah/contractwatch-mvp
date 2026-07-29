"""
Request ID generation + propagation. A contextvar carries the ID through
the whole request without threading it through every function signature —
the logging formatter picks it up automatically for every log line emitted
while handling that request, including from deep inside the check pipeline.
"""
import uuid
from contextvars import ContextVar

_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def set_request_id(request_id: str) -> None:
    _request_id_ctx.set(request_id)


def get_request_id() -> str | None:
    return _request_id_ctx.get()
