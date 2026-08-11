"""
Shared pytest fixtures.

Tests run against a dedicated `hsdg_mis_test` PostgreSQL database (never
the dev database), so they can freely create/drop data without touching
anything a developer is looking at locally. Table setup uses
`Base.metadata.create_all`/`drop_all` directly rather than running the
Alembic migration, which keeps the test suite fast and self-contained;
the migration itself is already verified separately (see
HANDOFF_TASK_0.md → Verification Performed).
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from app.db.base_class import Base
from app.db.session import get_db
from app import models as _models  # noqa: F401  (populate Base.metadata with all tables)
from app.main import app

TEST_DATABASE_URL = "postgresql+psycopg2://postgres:Sparsh%402005@localhost:5432/hsdg_mis_test"

engine = create_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


@pytest.fixture()
def db_session():
    """Fresh, empty schema for every test."""
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session: Session):
    """FastAPI TestClient wired to the isolated test database session."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
