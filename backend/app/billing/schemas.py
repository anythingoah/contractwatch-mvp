from pydantic import BaseModel, field_validator

VALID_PAID_PLANS = ("developer", "team")


class CheckoutRequest(BaseModel):
    plan: str

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, value: str) -> str:
        if value not in VALID_PAID_PLANS:
            raise ValueError(f"plan must be one of {VALID_PAID_PLANS}")
        return value


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class SubscriptionResponse(BaseModel):
    plan: str
    subscription_status: str | None
