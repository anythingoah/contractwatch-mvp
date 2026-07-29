"""
Central app configuration, loaded from environment variables.
Keep this the ONLY place that reads os.environ — everything else imports `settings`.

Fail-fast: DATABASE_URL and JWT_SECRET have no defaults. If they're not set,
pydantic-settings raises a ValidationError at import time (i.e. the app
refuses to start) instead of silently running with a placeholder secret —
that's a deliberate choice, not an oversight for the ones below with
defaults, which are genuinely optional.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_JWT_SECRETS = {"change-me-in-prod", "secret", "changeme", ""}


class Settings(BaseSettings):
    # Core — required, no defaults. App won't start without these set.
    database_url: str
    jwt_secret: str

    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Comma-separated list of allowed frontend origins. No wildcard default —
    # cookie-based auth requires an explicit origin, not "*", for the browser
    # to send credentials at all.
    cors_origins: str = "http://localhost:3000"

    # Cookie auth: set `cookie_secure=True` in production (requires HTTPS).
    cookie_name: str = "cw_token"
    cookie_secure: bool = False

    # Optional integrations — features degrade gracefully if unset
    openai_api_key: str | None = None
    email_api_key: str | None = None  # Resend or SendGrid key
    email_from: str = "alerts@contractwatch.dev"
    slack_webhook_default: str | None = None

    # Plan limits (free tier enforcement)
    free_plan_monitor_limit: int = 2
    free_plan_min_frequency_minutes: int = 24 * 60  # daily only

    # Rate limiting on auth endpoints (requests per window, per IP)
    auth_rate_limit_requests: int = 5
    auth_rate_limit_window_seconds: int = 60

    # Scheduler: set false when running the scheduler as a separate worker
    # process (see backend/worker.py) instead of embedded in the API process.
    # Must be false on every replica if you run more than one API instance,
    # or checks will fire once per replica.
    run_scheduler_in_app: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("jwt_secret")
    @classmethod
    def reject_insecure_jwt_secret(cls, v: str) -> str:
        if v.strip().lower() in INSECURE_JWT_SECRETS:
            raise ValueError(
                "JWT_SECRET is missing or set to an insecure placeholder. "
                "Set it to a long random string, e.g.: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return v


settings = Settings()
