"""
SQLAlchemy engine/session setup.
"""
import os
import re
from os import path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


def _expand_env(value: str | None, default: str | None = None) -> str | None:
    """Expand shell-style ${VAR} in value and return default if expansion left placeholders.

    This protects against environment values like "${PGPORT}" which can appear when a
    deployment platform writes a literal template instead of substituting it.
    """
    if value is None:
        return default
    # expand any $VAR or ${VAR} occurrences using the current environment
    expanded = os.path.expandvars(value)
    # If expansion didn't replace a ${...} placeholder, treat it as missing
    if "${" in expanded or "$(" in expanded:
        return default
    return expanded


# Build DATABASE_URL from individual Railway / Postgres variables (try multiple common names)
pg_user = _expand_env(os.getenv("PGUSER") or os.getenv("POSTGRES_USER"))
pg_password = _expand_env(os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD"))
pg_host = _expand_env(os.getenv("PGHOST") or os.getenv("POSTGRES_HOST"), "localhost")
pg_port = _expand_env(os.getenv("PGPORT") or os.getenv("POSTGRES_PORT"), "5432")
pg_db = _expand_env(os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB"))

# Debug: Print what we found (do NOT print passwords)
print(f"DEBUG PG vars - USER:{pg_user} HOST:{pg_host} PORT:{pg_port} DB:{pg_db}")

# Also try an explicit DATABASE_URL as fallback and expand any placeholders there too
env_db_url = os.getenv("DATABASE_URL")
raw_url = None
if env_db_url:
    raw_url = _expand_env(env_db_url)

if not raw_url and all([pg_user, pg_password, pg_host, pg_db]):
    # Build from individual vars
    raw_url = f"postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
elif raw_url and raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
elif raw_url and raw_url.startswith("postgresql://"):
    raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

# Mask password when printing the final URL for debug
def _mask_url(u: str | None) -> str:
    if not u:
        return "None"
    # mask the password if present: scheme://user:pass@ -> scheme://user:****@
    return re.sub(r"(://[^:]+):[^@]+@", r"\1:****@", u)

print(f"DEBUG - Final URL: {_mask_url(raw_url)[:80]}...")

if not raw_url:
    raise ValueError(
        "Cannot build DATABASE_URL! "
        f"Found: PGUSER={pg_user}, PGHOST={pg_host}, PGPORT={pg_port}, PGDATABASE={pg_db}. "
        "Check your deployment environment variables or set a full DATABASE_URL."
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
