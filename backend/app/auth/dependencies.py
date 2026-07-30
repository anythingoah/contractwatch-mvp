"""
`get_current_user` — the single dependency every protected route uses.

Reads the token from the httpOnly auth cookie (how the frontend authenticates)
and falls back to an `Authorization: Bearer` header (for scripts/CI/curl —
useful since this product's own customers may want to script against it).

Uses FastAPI's `Security`/`APIKeyCookie`/`HTTPBearer` classes to extract
both, rather than parsing `Request` by hand — not just style. Declaring
these as security schemes is what makes FastAPI mark protected routes as
requiring auth in the generated OpenAPI schema, which is what puts the
padlock icon + "Authorize" button on them in /docs. A hand-rolled
`Request`-parsing version works identically at runtime but is invisible to
the schema — every route silently looks public in `/docs` even though it
isn't, which undercuts the "interactive docs" pitch in the README's API
Documentation section. `auto_error=False` on both so a request with
neither present falls through to our own `_extract_token`-equivalent
check below and gets one consistent 401 message, instead of FastAPI's
generic 403 firing on whichever scheme happens to be checked first.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import decode_access_token
from app.models import User

cookie_scheme = APIKeyCookie(name=settings.cookie_name, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    cookie_token: str | None = Depends(cookie_scheme),
    bearer: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = cookie_token or (bearer.credentials if bearer else None)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user