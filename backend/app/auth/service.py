"""
Business logic for signup/login. Kept separate from the route handlers so it's
independently testable and so routes stay thin.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import User
from app.core.security import hash_password, verify_password, create_access_token


def signup(db: Session, email: str, password: str) -> tuple[str, User]:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return create_access_token(user.id), user


def login(db: Session, email: str, password: str) -> tuple[str, User]:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return create_access_token(user.id), user
