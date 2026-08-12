from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit
from app.auth.schemas import SignupRequest, LoginRequest, UserResponse
from app.auth.dependencies import get_current_user
from app.auth import service
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    """
    Auth token lives in an httpOnly cookie, not the response body — the
    frontend never touches the raw token, which closes off the XSS
    read-localStorage attack path. `secure` should be True in production
    (requires HTTPS); see settings.cookie_secure.
    """
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="none",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


@router.post("/signup", response_model=UserResponse, dependencies=[Depends(enforce_rate_limit)])
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    token, user = service.signup(db, payload.email, payload.password)
    _set_auth_cookie(response, token)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse, dependencies=[Depends(enforce_rate_limit)])
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    token, user = service.login(db, payload.email, payload.password)
    _set_auth_cookie(response, token)
    return UserResponse.model_validate(user)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.cookie_name, path="/")
    return {"status": "logged_out"}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    """Lets the frontend check 'am I logged in, and as who' without storing anything client-side."""
    return UserResponse.model_validate(user)
