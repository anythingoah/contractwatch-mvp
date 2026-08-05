from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.billing import service
from app.billing.schemas import CheckoutRequest, CheckoutResponse, PortalResponse, SubscriptionResponse
from app.core.database import get_db
from app.models import User

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout(payload: CheckoutRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return CheckoutResponse(checkout_url=service.create_checkout_session(db, user, payload.plan))


@router.get("/portal", response_model=PortalResponse)
def get_portal(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return PortalResponse(portal_url=service.create_portal_session(db, user))


@router.get("/subscription", response_model=SubscriptionResponse)
def get_subscription(user: User = Depends(get_current_user)):
    return SubscriptionResponse(plan=user.plan, subscription_status=user.subscription_status)


@router.post("/webhook", status_code=200)
async def webhook(request: Request, db: Session = Depends(get_db)):
    service.handle_webhook_event(db, await request.body(), dict(request.headers))
    return {"status": "received"}
