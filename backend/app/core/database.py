"""
SQLAlchemy engine/session setup.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Build DATABASE_URL from individual Railway Postgres variables
pg_user = os.getenv("PGUSER") or os.getenv("POSTGRES_USER")
pg_password = os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD")
pg_host = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST")
pg_port = os.getenv("PGPORT") or os.getenv("POSTGRES_PORT") or "5432"
pg_db = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB")

# Debug: Print what we found
print(f"DEBUG PG vars - USER:{pg_user} HOST:{pg_host} PORT:{pg_port} DB:{pg_db}")

# Also try Railway's own DATABASE_URL as fallback
raw_url = os.getenv("DATABASE_URL")

if not raw_url and all([pg_user, pg_password, pg_host, pg_db]):
    # Build from individual vars
    raw_url = f"postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
elif raw_url and raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
elif raw_url and raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

print(f"DEBUG - Final URL: {raw_url[:50]}...") # Only print first 50 chars to avoid leaking password

if not raw_url:
    raise ValueError(
        "Cannot build DATABASE_URL! "
        f"Found: PGUSER={pg_user}, PGHOST={pg_host}, PGPORT={pg_port}, PGDATABASE={pg_db}. "
        "Check Railway Postgres service variables."
    )

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
