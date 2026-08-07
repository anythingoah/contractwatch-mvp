"""Dodo Payments integration and webhook reconciliation."""
import logging

from dodopayments import DodoPayments, WebhookVerificationError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User

logger = logging.getLogger("contractwatch.billing")


def _client() -> DodoPayments:
    if not settings.dodo_payments_api_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Billing is not configured")
    return DodoPayments(bearer_token=settings.dodo_payments_api_key, environment=settings.dodo_payments_env)


def _product_id_for_plan(plan: str) -> str:
    product_id = {"developer": settings.dodo_product_id_developer, "team": settings.dodo_product_id_team}.get(plan)
    if not product_id:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"No Dodo product configured for plan '{plan}'")
    return product_id


def _plan_for_product_id(product_id: str | None) -> str | None:
    return {
        settings.dodo_product_id_developer: "developer",
        settings.dodo_product_id_team: "team",
    }.get(product_id) if product_id else None


def create_checkout_session(db: Session, user: User, plan: str) -> str:
    session = _client().checkout_sessions.create(
        product_cart=[{"product_id": _product_id_for_plan(plan), "quantity": 1}],
        return_url=f"{settings.frontend_url}/billing?checkout=success",
        metadata={"user_id": str(user.id), "plan": plan},
    )
    return session.checkout_url


def create_portal_session(db: Session, user: User) -> str:
    if not user.dodo_customer_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No billing account found for this user yet")
    session = _client().customers.portal.create(customer_id=user.dodo_customer_id)
    return session.portal_url


def handle_webhook_event(db: Session, raw_body: bytes, headers: dict[str, str]) -> None:
    client = _client()
    header_dict = {key: headers.get(key) for key in ("webhook-id", "webhook-timestamp", "webhook-signature")}

    try:
        event = client.webhooks.unwrap(
            payload=raw_body.decode("utf-8"), headers=header_dict, key=settings.dodo_payments_webhook_key,
        )
    except WebhookVerificationError as exc:
        logger.warning(
            "Webhook signature verification failed",
            extra={
                "cw_error_type": type(exc).__name__,
                "cw_error": repr(exc),
                "cw_body_length": len(raw_body),
                "cw_body_preview": raw_body[:200].decode("utf-8", errors="replace"),
                "cw_content_type": headers.get("content-type"),
                "cw_content_encoding": headers.get("content-encoding"),
            },
        )
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid webhook signature") from exc

    event_dict = event.model_dump() if hasattr(event, "model_dump") else event.dict()
    event_type = event_dict.get("type")
    data = event_dict.get("data") or {}
    metadata = data.get("metadata") or {}
    user_id = metadata.get("user_id")
    if not user_id:
        logger.info("Webhook event without user_id metadata", extra={"cw_event_type": event_type})
        return
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        logger.warning("Webhook event with invalid user_id", extra={"cw_event_type": event_type, "cw_user_id": user_id})
        return
    user = db.query(User).filter(User.id == user_id_int).first()
    if not user:
        logger.warning("Webhook event for unknown user_id", extra={"cw_event_type": event_type, "cw_user_id": user_id})
        return

    customer = data.get("customer") or {}
    if isinstance(customer, dict) and customer.get("customer_id"):
        user.dodo_customer_id = customer["customer_id"]
    if event_type in ("subscription.active", "subscription.renewed"):
        user.subscription_status = "active"
        user.plan = metadata.get("plan") or _plan_for_product_id(data.get("product_id")) or user.plan
    elif event_type == "subscription.on_hold":
        user.subscription_status = "past_due"
    elif event_type in ("subscription.cancelled", "subscription.expired"):
        user.subscription_status, user.plan = "canceled", "free"
    elif event_type == "subscription.failed":
        user.subscription_status = "failed"
    elif event_type == "subscription.plan_changed":
        user.plan = _plan_for_product_id(data.get("product_id")) or user.plan
        user.subscription_status = "active"
    elif event_type == "payment.failed":
        user.subscription_status = "past_due"
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    logger.info("Processed billing webhook", extra={"cw_event_type": event_type, "cw_user_id": user.id, "cw_new_status": user.subscription_status})
