"""
SQLAlchemy engine/session setup.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get and fix the database URL
raw_url = os.getenv("DATABASE_URL", "")

# Debug: Print what we're getting
print(f"DEBUG - Raw DATABASE_URL: {raw_url}")

# Fix Railway's postgres:// to postgresql+psycopg://
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
elif raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

# Fix empty port issue (like host:/dbname -> host:5432/dbname)
if raw_url and ":/" in raw_url.split("@")[-1]:
    raw_url = raw_url.replace(":/", ":5432/")

print(f"DEBUG - Fixed DATABASE_URL: {raw_url}")

if not raw_url:
    raise ValueError("DATABASE_URL is empty! Check Railway environment variables.")

engine = create_engine(raw_url, pool_pre_ping=True)
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
