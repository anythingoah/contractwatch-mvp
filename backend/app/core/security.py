"""
Password hashing + JWT issuing/verification. Deliberately minimal — no OAuth, no sessions table.

Uses PyJWT rather than python-jose: python-jose unconditionally depends on
`ecdsa` and `pyasn1` even with the `[cryptography]` extra installed, and
`ecdsa`'s known CVE (PYSEC-2026-1325, flagged by pip-audit) has no fix
version at all — it's not patchable, only avoidable. This app only ever
signs with HS256 (symmetric HMAC, no elliptic curve or RSA involved), and
PyJWT doesn't pull in ecdsa/pyasn1 for that algorithm — so switching
libraries removes the vulnerable dependency chain entirely rather than
carrying an unfixable transitive CVE indefinitely.
"""
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    """Returns the user_id encoded in the token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return int(payload.get("sub"))
    except (jwt.PyJWTError, ValueError, TypeError):
        return None