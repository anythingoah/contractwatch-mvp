"""
SQLAlchemy engine/session setup. Simple, no async — MVP doesn't need it yet.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# DEBUG: Print the actual URL (remove in production)
print(f"DEBUG - Raw DATABASE_URL from settings: {settings.database_url}")

# Quick validation
if not settings.database_url or settings.database_url.endswith(':/') or ':/@' in settings.database_url:
    raise ValueError(
        f"DATABASE_URL is malformed: '{settings.database_url}'. "
        f"Check Railway variables."
    )

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, always closed after the request."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
