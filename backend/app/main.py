"""
App entrypoint. Wires together auth + monitors routers, structured logging,
request ID tracking, centralized exception handling, security headers,
Prometheus metrics, and the background scheduler.

Table creation is via Alembic migrations (see backend/alembic/), not
create_all() — the Docker entrypoint runs `alembic upgrade head` before
starting the app. See README "Database Migrations" section.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.middleware import RequestContextMiddleware
from app.core.request_limits import CookieOriginProtectionMiddleware, RequestBodyLimitMiddleware
from app.core.exception_handlers import register_exception_handlers
from app.core.metrics import render_metrics
from app.auth.routes import router as auth_router
from app.billing.routes import router as billing_router
from app.monitors.routes import router as monitors_router
from app.scheduler.jobs import start_scheduler, stop_scheduler

configure_logging()
logger = logging.getLogger("contractwatch.main")

logger.info(
    "ContractWatch API configured",
    extra={
        "cw_environment": settings.environment,
        "cw_cookie_secure": settings.cookie_secure,
        "cw_cors_origins": settings.cors_origin_list,
    },
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # RUN_SCHEDULER_IN_APP=false when the scheduler runs as its own process
    # (backend/worker.py) instead of embedded here — required once you run
    # more than one API replica, or checks fire once per replica.
    if settings.run_scheduler_in_app:
        start_scheduler()
    else:
        logger.info("Embedded scheduler disabled (RUN_SCHEDULER_IN_APP=false) — expecting a separate worker process")
    yield
    if settings.run_scheduler_in_app:
        stop_scheduler()


app = FastAPI(title="ContractWatch API", version="0.1.0", lifespan=lifespan)

register_exception_handlers(app)

# Order matters: middleware runs outside-in on the way in, inside-out on the
# way out. RequestContextMiddleware goes first so every other layer (CORS,
# security headers, the routes themselves) logs under the same request_id.
app.add_middleware(RequestContextMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestBodyLimitMiddleware)
app.add_middleware(CookieOriginProtectionMiddleware)

app.add_middleware(
    CORSMiddleware,
    # No wildcard: cookie-based auth requires the browser to see an explicit
    # origin before it will send credentials. Set CORS_ORIGINS in .env —
    # comma-separated for multiple environments (e.g. staging + prod).
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(monitors_router)
app.include_router(billing_router)


@app.get("/health")
def health():
    """Used by deployment platforms / load balancers to check liveness."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint. Not authenticated — put it behind your
    reverse proxy / internal network in production, don't expose it publicly."""
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
