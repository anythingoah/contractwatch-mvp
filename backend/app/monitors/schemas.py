from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from email_validator import validate_email, EmailNotValidError

VALID_TYPES = ("rest", "mcp")
VALID_FREQUENCIES = ("daily", "hourly", "every_15_min")
VALID_CHANNEL_TYPES = ("slack", "email", "webhook")
VALID_TRANSPORTS = ("http", "sse")


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


class AlertChannelCreate(BaseModel):
    type: str  # "slack" | "email" | "webhook"
    configuration: dict

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in VALID_CHANNEL_TYPES:
            raise ValueError(f"channel type must be one of {VALID_CHANNEL_TYPES}")
        return v

    @model_validator(mode="after")
    def validate_configuration(self):
        cfg = self.configuration or {}
        if self.type == "slack":
            url = cfg.get("webhook_url", "")
            if not _is_http_url(url):
                raise ValueError("slack channel requires a valid 'webhook_url'")
        elif self.type == "webhook":
            url = cfg.get("url", "")
            if not _is_http_url(url):
                raise ValueError("webhook channel requires a valid 'url'")
        elif self.type == "email":
            try:
                validate_email(cfg.get("email", ""), check_deliverability=False)
            except EmailNotValidError as e:
                raise ValueError(f"invalid email address: {e}")
        return self


class MonitorCreate(BaseModel):
    name: str
    type: str  # "rest" | "mcp"
    frequency: str = "daily"  # "daily" | "hourly" | "every_15_min"

    # REST
    api_url: str | None = None
    openapi_spec_url: str | None = None

    # MCP
    mcp_server_url: str | None = None
    mcp_transport: str | None = "http"

    channels: list[AlertChannelCreate] = []

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        if len(v) > 100:
            raise ValueError("name must be 100 characters or fewer")
        if any(ord(char) < 32 or ord(char) == 127 for char in v):
            raise ValueError("name cannot contain control characters")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in VALID_TYPES:
            raise ValueError(f"type must be one of {VALID_TYPES}")
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v):
        if v not in VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {VALID_FREQUENCIES}")
        return v

    @field_validator("mcp_transport")
    @classmethod
    def validate_transport(cls, v):
        if v is not None and v not in VALID_TRANSPORTS:
            raise ValueError(f"mcp_transport must be one of {VALID_TRANSPORTS}")
        return v

    @model_validator(mode="after")
    def validate_source_urls(self):
        if self.type == "rest":
            if not self.openapi_spec_url or not _is_http_url(self.openapi_spec_url):
                raise ValueError("REST monitors require a valid 'openapi_spec_url'")
            if self.api_url and not _is_http_url(self.api_url):
                raise ValueError("'api_url' must be a valid http(s) URL")
        elif self.type == "mcp":
            if not self.mcp_server_url or not _is_http_url(self.mcp_server_url):
                raise ValueError("MCP monitors require a valid 'mcp_server_url'")
        return self


class MonitorResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    frequency: str
    last_checked: datetime | None
    created_at: datetime
    change_count: int = 0
    # Lets the frontend distinguish "just got its first check" (snapshot_count == 1,
    # nothing to compare yet) from "checked many times, happens to have zero drift" —
    # both look identical via change_count alone. See ActivityFeed.tsx.
    snapshot_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ChangeResponse(BaseModel):
    id: int
    change_type: str
    severity: str
    summary: str
    details: dict | None
    acknowledged: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecentChangeResponse(BaseModel):
    """
    Same shape as ChangeResponse, plus which monitor it belongs to — powers
    the dashboard's cross-monitor activity feed. Built manually in the route
    (not via model_validate/from_attributes), since monitor_name comes from
    a join, not a Change attribute.
    """
    id: int
    monitor_id: int
    monitor_name: str
    change_type: str
    severity: str
    summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CheckResult(BaseModel):
    status: str
    changes_detected: int
    breaking: bool
