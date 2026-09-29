import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.db.models import Base

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_client():
    Base.metadata.create_all(bind=engine)
    yield client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers(test_client):
    """Helper to create auth headers"""
    signup_response = test_client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "Test@Password123"},
    )
    token = signup_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2(test_client):
    """Helper to create auth headers for second user"""
    signup_response = test_client.post(
        "/auth/signup",
        json={"email": "test2@example.com", "password": "Test@Password123"},
    )
    token = signup_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
