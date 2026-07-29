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
        jwt_secret="a-sufficiently-long-random-secret",
        cors_origins="http://localhost:3000,https://contractwatch.com",
    )
    assert s.cors_origin_list == ["http://localhost:3000", "https://contractwatch.com"]


def test_cors_origins_single_value():
    s = Settings(database_url="postgresql://x/y", jwt_secret="a-real-secret", cors_origins="https://contractwatch.com")
    assert s.cors_origin_list == ["https://contractwatch.com"]


def test_cors_origins_strips_whitespace_around_commas():
    s = Settings(
        database_url="postgresql://x/y", jwt_secret="a-real-secret",
        cors_origins=" http://localhost:3000 , https://contractwatch.com ",
    )
    assert s.cors_origin_list == ["http://localhost:3000", "https://contractwatch.com"]


@pytest.mark.parametrize("insecure_value", ["change-me-in-prod", "secret", "changeme", ""])
def test_insecure_jwt_secret_rejected(insecure_value):
    with pytest.raises(ValidationError):
        Settings(database_url="postgresql://x/y", jwt_secret=insecure_value)


def test_missing_required_settings_raise_at_construction(monkeypatch):
    # Ensure the env vars used elsewhere aren't picked up by this test.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(ValidationError):
        Settings()  # no database_url, no jwt_secret — should fail, not silently default
