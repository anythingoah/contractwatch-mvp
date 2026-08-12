"""
Shared test fixtures. Uses an in-memory SQLite DB instead of Postgres —
fast, zero setup, and the models don't use any Postgres-specific features.
If you later rely on Postgres-only behavior (e.g. JSONB operators), switch
this to a real throwaway Postgres via testcontainers.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.core.rate_limit import reset_rate_limit
from app.main import app
from app import models  # noqa: F401 — ensure models are registered on Base


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite doesn't enforce FK constraints by default — turn them on so
    # cascade-delete behavior matches Postgres in tests.
    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Every TestClient shares the same source IP, so rate-limit state leaks
    # across tests unless we reset it before each one.
    reset_rate_limit()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_client(client):
    """A TestClient that's already signed up and logged in (cookie set)."""
    # Signup to create the user and get the auth cookie
    resp = client.post("/auth/signup", json={"email": "test@example.com", "password": "password123"})
    assert resp.status_code == 200, f"Signup failed: {resp.status_code} - {resp.text}"
    # The TestClient automatically stores and sends cookies for subsequent requests
    return client
