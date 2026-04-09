"""
Test Configuration and Fixtures for ZTNAS
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Force a test-safe environment before importing application settings/main.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-1234567890")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Import after path setup
from config.database import Base, get_db

# Create test engine with StaticPool to ensure all connections use the same in-memory database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    
    yield db_session
    
    db_session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """Create test client with database override"""
    from main import app

    def override_get_db():
        try:
            yield db
        finally:
            pass  # Don't close the db as it's managed by the fixture
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user credentials"""
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "TestPassword@123"
    }


@pytest.fixture
def test_admin_data():
    """Test admin credentials"""
    return {
        "email": "admin@example.com",
        "username": "admin",
        "password": "AdminPassword@123"
    }


@pytest.fixture
def auth_token(client: TestClient, test_user_data):
    """Get authentication token for test user"""
    # Register user
    client.post("/api/v1/auth/register", json=test_user_data)
    
    # Login using username (not email)
    response = client.post("/api/v1/auth/login", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    
    if response.status_code != 200:
        raise ValueError(f"Login failed: {response.text}")
    
    return response.json().get("access_token")


@pytest.fixture
def admin_token(client: TestClient, test_admin_data):
    """Get authentication token for admin user"""
    # Register admin
    client.post("/api/v1/auth/register", json=test_admin_data)
    
    # Login using username (not email)
    response = client.post("/api/v1/auth/login", json={
        "username": test_admin_data["username"],
        "password": test_admin_data["password"]
    })
    
    if response.status_code != 200:
        raise ValueError(f"Admin login failed: {response.text}")
    
    return response.json().get("access_token")


@pytest.fixture
def auth_headers(auth_token):
    """Get Authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Get Admin Authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}
