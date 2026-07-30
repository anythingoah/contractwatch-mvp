# ContractWatch

**Uptime monitoring for API contracts.** ContractWatch watches your REST APIs
and MCP servers and alerts you the instant their contract drifts — a
parameter goes missing, a type changes, a tool gets removed — via Slack,
email, or webhook.

It is not an API gateway, not a governance platform, not a security scanner.
It does one thing: tells you when something that used to work will now break.

## Architecture

```
contractwatch/
├── backend/          FastAPI app (see below)
│   └── worker.py      standalone scheduler process (optional, see Deployment)
├── frontend/          Next.js app (Tailwind, dark mode)
├── docker-compose.yml
└── .env.example
```

**Backend modules** (`backend/app/`):
- `auth/` — email/password signup & login, JWT issued as an httpOnly cookie (not returned in the response body)
- `models.py` — all SQLAlchemy models (users, monitors, snapshots, changes, alert_channels), with indexes matching actual query patterns
- `monitors/` — CRUD + validation + the core check pipeline (`service.run_check`)
- `fetchers/` — REST (OpenAPI URL/JSON/YAML) and MCP (`tools/list`) contract retrieval
- `diff_engine/` — pure, dependency-free normalization + comparison + severity classification
- `alerts/` — Slack, email (Resend), webhook senders + optional OpenAI explanation
- `scheduler/` — APScheduler background loop that runs due checks every minute; splittable into a standalone worker process (see Deployment)
- `core/logging_config.py` — structured JSON logging to stdout
- `core/rate_limit.py` — in-memory per-IP rate limiting on auth endpoints
- `core/security_headers.py` — baseline security headers middleware

**The check pipeline** (`monitors/service.py: run_check`):
1. Fetch the current contract (OpenAPI spec or MCP tool list)
2. Normalize it into a canonical shape (`diff_engine/normalize.py`)
3. Hash it — if unchanged since the last snapshot, stop here (cheap path)
4. Otherwise diff against the previous snapshot (`diff_engine/engine.py`)
5. Classify each change as `critical` / `warning` / `info` via a fixed rule table
6. Store the changes, update monitor status, dispatch alerts to configured channels

Severity is **always rule-based, never AI-judged** — the optional OpenAI
explanation (see `alerts/ai_explain.py`) only adds a plain-English "why this
matters" note on top of an already-classified breaking change. If
`OPENAI_API_KEY` is unset, this feature is silently skipped and everything
else works identically.

## Local Setup

**Requirements:** Docker + Docker Compose.

```bash
cp .env.example .env
# edit .env — at minimum set JWT_SECRET to something random
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:3000
- Postgres: localhost:5432 (user/pass/db: `contractwatch`)

On `docker compose up`, the backend container runs `alembic upgrade head`
before starting (see `backend/entrypoint.sh`) — schema is managed by
migrations, not `create_all()`.

### Database Migrations (Alembic)

```bash
cd backend
# after changing a model, generate a migration:
alembic revision --autogenerate -m "describe the change"
# review the generated file in alembic/versions/ before applying —
# autogenerate is a good first draft, not always a correct one
alembic upgrade head
```

The initial migration (`alembic/versions/0001_initial_schema.py`) already
creates every table plus the composite indexes described below.

### Running the backend without Docker

```bash
cd backend
python -m venv venv

# macOS/Linux:
source venv/bin/activate
# Windows (cmd):
venv\Scripts\activate.bat
# Windows (PowerShell):
venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload
```

You'll need a local Postgres and to point `DATABASE_URL` at it — use the
`postgresql+psycopg://` scheme (not bare `postgresql://`), e.g.
`postgresql+psycopg://user:pass@localhost:5432/contractwatch`. The
`+psycopg` tells SQLAlchemy to use the psycopg3 driver this project
installs; a bare `postgresql://` URL will fail at connection time since
plain psycopg2 isn't installed (see requirements.txt for why).

**If VS Code/Pylance shows "Import could not be resolved" for `sqlalchemy`,
`fastapi`, etc.** — that's not a code problem, every module in this
codebase imports the same way. It means Pylance is checking against a
different Python interpreter than the one `pip install -r requirements.txt`
ran in (e.g. it's using system Python instead of `backend/venv`). Fix:
`Ctrl+Shift+P` → "Python: Select Interpreter" → pick the one at
`backend/venv/Scripts/python.exe` (Windows) or `backend/venv/bin/python`
(macOS/Linux), then reload the window. If that interpreter doesn't appear
in the list, the venv wasn't actually created/activated when `pip install`
ran — redo the block above from a shell that shows `(venv)` in the prompt
after activation.

### Running the tests

```bash
cd backend
pip install -r requirements.txt
```

Settings fail fast if `DATABASE_URL`/`JWT_SECRET` aren't set — dummy values
are fine for tests, since the DB dependency is overridden with in-memory
SQLite (`conftest.py`):

```bash
# macOS/Linux:
DATABASE_URL=postgresql+psycopg://test:test@localhost/test JWT_SECRET=test-only-secret pytest tests/ -v

# Windows (cmd):
set DATABASE_URL=postgresql+psycopg://test:test@localhost/test && set JWT_SECRET=test-only-secret && pytest tests/ -v

# Windows (PowerShell):
$env:DATABASE_URL="postgresql+psycopg://test:test@localhost/test"; $env:JWT_SECRET="test-only-secret"; pytest tests/ -v
```

Coverage:
- `test_diff_engine.py` — pure fixture tests, no DB, no mocking needed
- `test_config.py` — CORS origin parsing, fail-fast on missing/insecure secrets
- `test_auth.py` — signup/login/logout, duplicate email, cookie session, `/auth/me`
- `test_monitors.py` — CRUD, URL/email/frequency validation, plan-limit enforcement, per-user isolation
- `test_alerts.py` — dispatch fan-out, one channel failing doesn't block others, missing-provider fail-soft
- `test_check_pipeline.py` — end-to-end `run_check`: baseline creation, drift detection, no-op on unchanged contract, unreachable handling
- `test_scheduler.py` — due/not-due logic, only due monitors get checked, inactive monitors skipped, one failing check doesn't block others

Tests run against an in-memory SQLite DB (see `tests/conftest.py`), not
Postgres — fast and zero-setup, but revisit with a real throwaway Postgres
(e.g. `testcontainers`) if you start relying on Postgres-only behavior.
Network calls (fetchers, Slack/webhook senders) are monkeypatched, never
hit for real. CI runs this suite on every PR that touches `backend/`
(`.github/workflows/backend-tests.yml`).

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | **Yes — app refuses to start without it** | Postgres connection string — must use the `postgresql+psycopg://` scheme, see "Running the backend without Docker" |
| `JWT_SECRET` | **Yes — app refuses to start without it, or if left as an insecure placeholder** | Signs auth tokens. Generate one: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `COOKIE_SECURE` | No (default `false`) | Set `true` once served over HTTPS — required for the auth cookie to be sent in production |
| `CORS_ORIGINS` | Yes | Comma-separated list of frontend origins allowed to call the API — no wildcard is supported, cookie auth requires an explicit origin |
| `AUTH_RATE_LIMIT_REQUESTS` / `AUTH_RATE_LIMIT_WINDOW_SECONDS` | No (default `5` / `60`) | Rate limit on `/auth/signup` and `/auth/login`, per IP |
| `RUN_SCHEDULER_IN_APP` | No (default `true`) | Set `false` on every replica if you split the scheduler into `worker.py` — see "Deployment" |
| `OPENAI_API_KEY` | No | Enables AI explanations on breaking changes |
| `SLACK_WEBHOOK` | No | Default Slack webhook (channels can also set their own per-monitor) |
| `EMAIL_API_KEY` | No | Resend API key — email alerts are skipped without it |
| `EMAIL_FROM` | No | From-address for email alerts |
| `NEXT_PUBLIC_API_URL` | Yes (frontend) | Where the frontend points its API calls |

## API Documentation

Interactive docs (try-it-out included) are auto-generated by FastAPI at
`/docs` once the backend is running — that's the fastest way to explore the
full schema. Protected routes show a padlock icon there; click "Authorize"
and paste a token (or just log in via `/auth/login` from another tab first —
same-origin requests from `/docs` carry the auth cookie automatically) to
try them directly. What follows is the reference a human reads once.

### Authentication flow

```
┌────────┐  1. POST /auth/signup {email, password}   ┌─────────┐
│ Browser│ ─────────────────────────────────────────▶ │ Backend │
│        │ ◀───────────────────────────────────────── │         │
└────────┘  2. Set-Cookie: cw_token=<jwt>; HttpOnly     └─────────┘
     │          Secure; SameSite=Lax           (body: the User, no token)
     │
     │  3. Every subsequent request automatically includes the
     │     cookie (credentials: "include") — the frontend never
     │     reads, stores, or touches the raw token itself.
     ▼
┌────────┐  GET /monitors  (cookie sent automatically)  ┌─────────┐
│ Browser│ ─────────────────────────────────────────▶  │ Backend │
└────────┘                                               └─────────┘
```

Scripts/CI/curl that can't hold cookies can instead pass
`Authorization: Bearer <token>` — the same `get_current_user` dependency
accepts either, cookie first, header as fallback. There's no separate
"API token" concept in this MVP: it's the same JWT either way, you just
have to get it out of `Set-Cookie` yourself if you're not a browser.

### Example: signup → create a monitor → check it

```bash
# 1. Sign up (cookie jar captures the auth cookie for subsequent calls)
curl -c cookies.txt -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "a-real-password"}'
```
```json
{"id": 1, "email": "you@example.com", "plan": "free"}
```

```bash
# 2. Create an MCP monitor with a Slack alert channel
curl -b cookies.txt -X POST http://localhost:8000/monitors \
  -H "Content-Type: application/json" \
  -d '{
        "name": "GitHub MCP Server",
        "type": "mcp",
        "frequency": "daily",
        "mcp_server_url": "https://mcp.example.com",
        "channels": [{"type": "slack", "configuration": {"webhook_url": "https://hooks.slack.com/services/..."}}]
      }'
```
```json
{
  "id": 7,
  "name": "GitHub MCP Server",
  "type": "mcp",
  "status": "pending",
  "frequency": "daily",
  "last_checked": null,
  "created_at": "2026-07-28T09:12:03Z",
  "change_count": 0
}
```

```bash
# 3. Trigger an immediate check instead of waiting for the schedule
curl -b cookies.txt -X POST http://localhost:8000/monitors/7/check
```
```json
{"status": "baseline_created", "changes_detected": 0, "breaking": false}
```

```bash
# 4. Later, after the contract has drifted:
curl -b cookies.txt http://localhost:8000/monitors/7/changes
```
```json
[
  {
    "id": 3,
    "change_type": "removed_parameter",
    "severity": "critical",
    "summary": "Removed required parameter 'currency' from create_invoice",
    "details": {"old_value": "currency", "new_value": null, "path": "create_invoice.currency"},
    "acknowledged": false,
    "created_at": "2026-07-28T14:02:11Z"
  }
]
```

### Error response format

Every non-2xx response has the same shape, whether it's a deliberate
`HTTPException` (404, 401, 402, 429) or an unhandled exception (500) — see
`core/exception_handlers.py`:

```json
{
  "detail": "Monitor not found",
  "request_id": "7d3c2a9f1b4e"
}
```

`request_id` matches the `X-Request-ID` response header and every backend
log line for that request — quote it in a bug report and every relevant
log line is one grep away.

Validation errors (422) have a slightly richer `detail` — FastAPI's
standard field-level format:

```json
{
  "detail": [
    {"type": "value_error", "loc": ["body", "openapi_spec_url"], "msg": "REST monitors require a valid 'openapi_spec_url'"}
  ],
  "request_id": "9f1b4e7d3c2a"
}
```

### Route reference

```
POST   /auth/signup                  {email, password} -> User, sets httpOnly auth cookie   [rate-limited]
POST   /auth/login                   {email, password} -> User, sets httpOnly auth cookie   [rate-limited]
POST   /auth/logout                  -> clears the auth cookie
GET    /auth/me                      -> current User (also doubles as an auth check)

GET    /monitors                     -> list your monitors
POST   /monitors                     -> create a monitor (see MonitorCreate schema)
GET    /monitors/{id}                -> monitor detail
DELETE /monitors/{id}
POST   /monitors/{id}/check          -> trigger an immediate check
GET    /monitors/{id}/changes        -> change history, newest first

GET    /health                       -> liveness check (used by Docker/load balancers)
GET    /metrics                      -> Prometheus scrape endpoint (see Deployment — not for public exposure)
```

All routes except `/auth/signup` and `/auth/login` require authentication.
`/auth/signup` and `/auth/login` are rate-limited per IP (default: 5
requests/60s, configurable via `AUTH_RATE_LIMIT_*`) — a `429` is returned
past that. It's an in-memory limiter (see `core/rate_limit.py`), which
carries the same single-process caveat as the scheduler below.

Every response is the requested resource directly (`Monitor`, `User`,
`Change[]`, etc.) — no `{data, message, errors}` envelope. That's a
deliberate, consistent choice for this API, not an oversight: FastAPI's
generated OpenAPI schema is more useful per-endpoint without a wrapper, and
errors already have one consistent shape (above). If you add a public/
versioned API surface later where clients need to distinguish "empty
result" from "partial failure" in one payload, an envelope becomes worth
it — not yet.

## Architecture Decisions

Short version of why the codebase looks the way it does — useful context
if you're reading this as a portfolio piece, or deciding whether to follow
the same choices in your own project.

**Why APScheduler instead of Celery?**
The workload is periodic and I/O-bound (poll a URL every N minutes), not
queue-driven — there's no producer generating a variable stream of jobs
that needs backpressure, prioritization, or distributed workers. APScheduler
gets a working scheduler running in about 20 lines with zero extra
infrastructure (no Redis/RabbitMQ broker). The tradeoff is explicit and
documented (see "Deployment" above): it's single-process, so it stops being
the right choice once you need more than one API replica or a check volume
one process can't tick through in its interval — at that point, Celery +
Redis beat is the right migration, and the module boundary
(`scheduler/jobs.py`) is drawn specifically so that swap doesn't touch
`monitors/`, `diff_engine/`, or `alerts/`.

**Why SQLAlchemy instead of raw SQL?**
The query surface here is almost entirely simple CRUD plus a handful of
filtered lookups (owner-scoped monitors, due-for-check monitors, change
history) — exactly what an ORM is good at, with the bonus of Alembic's
autogenerate diffing models against the DB. Raw SQL would earn its keep if
this had complex reporting joins or hand-tuned query plans to maintain;
it doesn't, and "the model is the schema" keeps migrations and application
code from drifting apart.

**Why FastAPI?**
Async-native, generates OpenAPI/JSON-Schema directly from Pydantic models
(which is what powers the interactive `/docs` and the validation errors
above), and has a dependency-injection system (`Depends(get_db)`,
`Depends(get_current_user)`) that keeps auth/DB-session wiring out of
route bodies without needing a framework-level "service container." For a
product whose actual value is REST/OpenAPI monitoring, using a framework
that treats OpenAPI as a first-class citizen isn't just convenient, it's
on-theme.

**Why request IDs?**
Once alerts, scheduled checks, and manual API calls all write to the same
log stream, "why did this check fail" becomes a multi-line search problem
without something to `grep` on. A request ID costs one contextvar and one
middleware, and turns "search the logs around this timestamp" into "search
this exact ID" — worth it well before you have a large enough team or
volume to justify a full tracing stack (OpenTelemetry, Jaeger, etc.).

**Why cookie-based auth instead of a token in localStorage/response body?**
`localStorage` is readable by any JavaScript running on the page — a
single XSS vulnerability anywhere in the frontend (including a
third-party script) can exfiltrate every logged-in user's token. An
httpOnly cookie is invisible to JavaScript entirely; the tradeoff is CSRF
exposure, mitigated here with `SameSite=Lax` (blocks the common
cross-site-POST attack shape) plus strict, no-wildcard CORS (see
"Deployment"). For a product handling API/MCP contract data rather than
payments or PII, this is a reasonable point on the security/complexity
curve — full CSRF tokens would be the next step up if that calculus changes.

**Why isn't `starlette` pinned directly in `requirements.txt`, given it had CVEs?**
It's a transitive dependency — `fastapi` requires a specific `starlette`
range internally, and that range is part of what "this fastapi version
works" means. Pinning `starlette` independently can produce a combination
fastapi's own maintainers never tested, or a resolver conflict outright.
The correct lever for a transitive-dependency CVE is bumping the direct
dependency (`fastapi`) and letting it pull in whatever `starlette` version
it actually requires — if no fastapi release yet requires the patched
`starlette`, the fix has to wait on fastapi upstream, not get forced here.
(First draft of this fix got this wrong — pinned `starlette` directly — and
that was corrected after review; kept as `## Code Review Follow-ups` Round
5 rather than quietly rewritten, since the mistake and the correction are
both useful information for whoever reads this next.)

## Deployment

The `docker-compose.yml` here is suitable for a single-VM deployment
(Hetzner, Fly.io, Railway, DigitalOcean — pick one). For production:

1. Use a managed Postgres instead of the `db` service (backups, failover).
2. Set `CORS_ORIGINS` in `.env` to your actual frontend domain — there is
   no wildcard fallback, by design (cookie auth needs an explicit origin).
3. Set `COOKIE_SECURE=true` once you're serving over HTTPS.
4. Put the backend behind Cloudflare/a reverse proxy for TLS. Baseline
   security headers (`X-Content-Type-Options`, `X-Frame-Options`, CSP,
   `Referrer-Policy`) are already applied by `SecurityHeadersMiddleware` —
   nothing to add here unless your reverse proxy needs different values.
5. Migrations already run automatically via `entrypoint.sh` on container
   start — for zero-downtime deploys, run `alembic upgrade head` as a
   separate release step before rolling the new backend version out,
   rather than relying on container startup ordering.
6. **Scheduler**: the embedded APScheduler (`RUN_SCHEDULER_IN_APP=true`,
   the default) only works correctly with exactly one backend replica. If
   you scale to multiple replicas, set `RUN_SCHEDULER_IN_APP=false` on all
   of them and run the scheduler as its own process instead:
   `docker compose --profile worker up worker` (see `backend/worker.py`).
   This still isn't horizontally scalable on its own — it's one process
   ticking every monitor — but it decouples scheduling from API uptime/
   replica count. Move to Celery + Redis beat once check volume outgrows
   a single worker process; the module boundary in `scheduler/jobs.py`
   means that swap doesn't touch `monitors/`, `diff_engine/`, or `alerts/`.
7. The in-memory auth rate limiter (`core/rate_limit.py`) has the same
   single-process assumption — move it to Redis at the same time you split
   the scheduler, or it under-counts across replicas.

## Plan Limits (enforced server-side)

| Plan | Monitors | Frequencies |
|---|---|---|
| Free | 2 | Daily |
| Developer ($19/mo) | 20 | Daily, Hourly |
| Team ($49/mo) | Unlimited | Daily, Hourly, Every 15 min |

Enforcement lives in `monitors/service.py: _enforce_plan_limits` — there is
no Stripe billing integration wired up yet in this build (plan is a plain
string field on `User`, settable directly for now). Wiring Stripe checkout +
webhooks to flip `user.plan` is the natural next step before charging real
customers.

## Code Review Follow-ups

This build has been through seven rounds of review.

**Round 1** — CORS restricted to explicit origins; Alembic migrations
replace `create_all()`; auth token moved to an httpOnly cookie; typed
TypeScript API client; frontend `ApiError` handling with timeouts; URL/
email/frequency/channel validation; structured JSON logging; test suite
expanded from diff-engine-only to auth, monitors, alerts, and the full
check pipeline.

**Round 2:**
- Fail-fast settings: `DATABASE_URL`/`JWT_SECRET` are now required with no
  default, and an insecure placeholder secret is explicitly rejected —
  the app won't start misconfigured, it errors immediately with a clear message
- Rate limiting on `/auth/signup` and `/auth/login` (in-memory, per-IP)
- Security headers middleware (`X-Content-Type-Options`, `X-Frame-Options`,
  CSP, `Referrer-Policy`, `Permissions-Policy`) on every response
- Scheduler split into a real standalone option (`backend/worker.py` +
  `RUN_SCHEDULER_IN_APP` flag + `docker compose --profile worker`), not
  just a README note — `is_due`/`run_due_checks` extracted as pure,
  testable functions in the process
- Test suite extended: `test_scheduler.py` (due/not-due logic, inactive
  monitors skipped, one failure doesn't block others) and `test_config.py`
  (verified the CORS comma-parsing explicitly flagged in review, plus
  fail-fast behavior)
- Added `.gitignore` (missing until now — notable once `.env` holds a
  required real secret) and documented consistent API response shape
  (resource directly, no envelope — see "API Documentation" for the reasoning)

**Round 3:**
- Request IDs on every request (`X-Request-ID` header + attached to every
  log line for that request via a contextvar), see `core/request_context.py`
  and `core/middleware.py`
- Centralized exception handling (`core/exception_handlers.py`) — one place
  logs unhandled exceptions with full context and returns a consistent
  `{"detail", "request_id"}` shape for every error, expected or not
- Prometheus metrics at `GET /metrics` — request count/duration, scheduler
  jobs executed, failed checks, alerts sent by channel/outcome
- Retry with exponential backoff (`tenacity`) on both fetchers, transient
  failures only (timeouts/connection errors/5xx) — never retries a 4xx
- Graceful shutdown: scheduler waits for in-flight checks (`wait=True`);
  `worker.py` handles `SIGTERM` (what Docker/Kubernetes actually send on
  stop), not just Ctrl-C
- Docker health checks on both containers; `frontend` now waits on
  `backend`'s actual health, not just container start
- Declined to build persisted audit logging — the product spec explicitly
  excludes "audit logs" as enterprise-governance scope creep; structured
  logs with request IDs give traceability on create/delete actions without
  a compliance-feature footprint

**Round 4:**
- Security scanning: Dependabot (`.github/dependabot.yml`, covers pip/npm/
  GitHub Actions/Docker base images), `pip-audit` and `npm audit` on every
  PR plus a weekly schedule (catches newly-disclosed CVEs in dependencies
  that haven't changed), and CodeQL static analysis for Python + TS —
  see `.github/workflows/security-scan.yml`
- API documentation expanded: auth flow diagram, real curl request/response
  examples end-to-end (signup → create monitor → check → view drift), the
  error response format (including the request-ID tie-in above), and a full
  route reference
- Added this "Architecture Decisions" section below, explaining the
  APScheduler/SQLAlchemy/FastAPI/request-ID/cookie-auth choices

**Round 5** — the security scanning added in Round 4 did its job: the first
real CI run of `pip-audit` found 14 known vulnerabilities across 3 packages.
Fixed by addressing root cause rather than just bumping numbers:
- Replaced `python-jose` with `PyJWT`. `python-jose` unconditionally pulls
  in `ecdsa` and `pyasn1` even with the `[cryptography]` extra installed;
  `ecdsa`'s flagged CVE (`PYSEC-2026-1325`) has **no fix version at all** —
  it's not patchable, only avoidable. This app only ever signs HS256
  (symmetric HMAC — no elliptic curve or RSA involved anywhere in the
  codebase), and PyJWT doesn't pull in ecdsa/pyasn1 for that algorithm, so
  the switch removes the entire vulnerable dependency chain instead of
  carrying an unfixable transitive CVE indefinitely. Verified the
  encode/decode round trip (including expired-token and wrong-secret error
  paths) against the actual installed PyJWT before treating this as done —
  see the note in `core/security.py`.
- `starlette` (pulled in transitively via `fastapi`) had several CVEs
  fixed across versions up to `1.3.1`. First attempt at this pinned
  `starlette>=1.3.1` directly — wrong, caught in review: `starlette` isn't
  a direct dependency, `fastapi` manages which version it needs, and
  overriding that independently risks either a resolver conflict or,
  worse, silently installing a fastapi/starlette combination that's never
  actually been tested together upstream. Corrected to just bumping the
  `fastapi` floor (`>=0.116.1`) and letting pip resolve `starlette`
  naturally from fastapi's own requirements. **Residual risk, stated
  plainly:** if the fastapi version pip resolves still carries the
  flagged `starlette` CVE, that means no fastapi release yet requires a
  patched `starlette` — the correct move at that point is to wait for
  upstream fastapi (or open an issue there), not to force an untested
  starlette version. This can't be fully closed out here: I have no
  network access in this sandbox to run the actual resolution, so CI's
  `pip-audit` is the real verification, not this writeup.

**Round 6** — `auth/dependencies.py` extracted the cookie/header token by
hand-parsing `Request` directly. That works identically at runtime, but
because it isn't declared as a FastAPI `Security` dependency, none of the
protected routes showed up as requiring auth in the generated OpenAPI
schema — no padlock icon, no "Authorize" button in `/docs`, every endpoint
looked publicly callable in the schema even though it wasn't. Undercut the
"interactive docs" claim made in this README's own API Documentation
section. Fixed by declaring `APIKeyCookie` and `HTTPBearer` as proper
security schemes (`auto_error=False` on both, so a request with neither
falls through to one consistent 401 rather than FastAPI's generic 403);
behavior is identical, but `/docs` now accurately reflects which routes
need auth and lets you paste a token in the Authorize dialog to test them.
Added `test_bearer_header_works_without_cookie` and two related cases to
`test_auth.py` — the previous suite only ever exercised the cookie path
via the `auth_client` fixture, never the header fallback this change
touched directly.

**Round 7** — a real Windows install hit `pip install -r requirements.txt`
failing to build `psycopg2-binary` from source (`pg_config` not found).
Root cause: `psycopg2-binary` is in maintenance-only mode and its wheel
coverage lags new CPython releases significantly — on a recent Python
version with no matching wheel, pip falls back to building from source,
which needs PostgreSQL's dev tools installed locally just to set up a
Python venv. Switched to `psycopg[binary]` (psycopg3), which is actively
maintained and ships wheels for new Python versions much faster. This
touched every `DATABASE_URL` in the repo — psycopg3 needs the
`postgresql+psycopg://` scheme, not bare `postgresql://` (SQLAlchemy uses
the URL scheme to pick the driver) — updated in `docker-compose.yml`,
`.env.example`, `.github/workflows/backend-tests.yml`, and every example
in this README. Deliberately did **not** touch `backend/Dockerfile`'s
`gcc`/`libpq-dev` install, even though psycopg3's binary wheels likely
make them unnecessary now — that's an unverified guess about build
requirements in a container I can't actually build here, exactly the
category of mistake the `starlette` pin was in Round 5. Flagged as a
"worth checking, not changed" item below instead of repeating that.

Still open:
- `backend/Dockerfile` still installs `gcc`/`libpq-dev` for what was
  psycopg2's benefit — psycopg3's binary wheels probably don't need them
  anymore, meaning the image could get smaller/build faster, but this
  needs an actual `docker compose build` to confirm before removing them,
  not another guess from this sandbox.
- The `starlette` CVEs pip-audit flagged may not be fully resolved by the
  `fastapi>=0.116.1` bump alone — depends on whether any released fastapi
  version requires a patched starlette yet. Needs a real CI `pip-audit`
  run to confirm either way; not something this sandbox can verify.
- No duplicate-monitor-name check per user (validation, not currently enforced)
- No refresh-token rotation — the auth cookie is a single long-lived token; fine for MVP, revisit before this handles anything more sensitive than "when did my API schema change"
- Rate limiter and scheduler both carry the same single-process assumption — documented in "Deployment," not yet solved with Redis
- `models.py` is still one file — right call at this size per the original review, revisit once it grows past ~6-8 tables
- No CI lint/format check or automated migration-verification step yet (flagged in review, not yet built — `backend-tests.yml` runs tests only)

## What's Deliberately Not Here

Per the product spec: no RBAC, no SSO, no organizations, no audit logs, no
compliance dashboards, no security scanning. If you find yourself about to
add one of these, stop and ask whether a customer actually asked for it.
#