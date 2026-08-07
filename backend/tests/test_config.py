"""
Settings validation: CORS origin parsing (explicitly flagged for
verification in review) and fail-fast behavior on insecure/missing secrets.
"""
import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_parses_comma_separated_list():
    s = Settings(
        database_url="postgresql://x/y",
        jwt_secret="a-sufficiently-long-random-secret-value",
        cors_origins="http://localhost:3000,https://contractwatch.com",
    )
    assert s.cors_origin_list == ["http://localhost:3000", "https://contractwatch.com"]


def test_cors_origins_single_value():
    s = Settings(
        database_url="postgresql://x/y",
        jwt_secret="a-sufficiently-long-random-secret-value",
        cors_origins="https://contractwatch.com",
    )
    assert s.cors_origin_list == ["https://contractwatch.com"]


def test_cors_origins_strips_whitespace_around_commas():
    s = Settings(
        database_url="postgresql://x/y",
        jwt_secret="a-sufficiently-long-random-secret-value",
        cors_origins=" http://localhost:3000 , https://contractwatch.com ",
    )
    assert s.cors_origin_list == ["http://localhost:3000", "https://contractwatch.com"]


@pytest.mark.parametrize("insecure_value", ["change-me-in-prod", "secret", "changeme", ""])
def test_insecure_jwt_secret_rejected(insecure_value):
    with pytest.raises(ValidationError):
        Settings(database_url="postgresql://x/y", jwt_secret=insecure_value)


def test_short_jwt_secret_rejected():
    with pytest.raises(ValidationError):
        Settings(database_url="postgresql://x/y", jwt_secret="too-short")


def test_production_rejects_wildcard_cors():
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql://x/y",
            jwt_secret="a-sufficiently-long-random-secret-value",
            environment="production",
            cookie_secure=True,
            cors_origins="*",
        )


def test_production_requires_secure_cookies():
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql://x/y",
            jwt_secret="a-sufficiently-long-random-secret-value",
            environment="production",
            cookie_secure=False,
            cors_origins="https://contractwatch.com",
        )


def test_missing_required_settings_raise_at_construction(monkeypatch):
    # Ensure the env vars used elsewhere aren't picked up by this test.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # no database_url, no jwt_secret — should fail, not silently default

def test_env_example_placeholder_is_rejected():
    """
    Regression test: a real secret-length placeholder that isn't in an
    exact-match blocklist previously passed validation. This asserts the
    literal .env.example placeholder is always rejected, so this can't
    silently reappear if that file's wording changes again.
    """
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql://x/y",
            jwt_secret="REPLACE_ME_generate_with_python_secrets_token_urlsafe_48",
        )