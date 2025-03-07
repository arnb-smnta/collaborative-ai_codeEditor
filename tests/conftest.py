import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from auth import get_db
from models import Base
from main import app
from fastapi.testclient import TestClient

# ✅ Set up test database (SQLite for testing)
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ✅ Override FastAPI's database dependency
@pytest.fixture(scope="session")
def db_session():
    """Provides a fresh test database session"""
    Base.metadata.drop_all(bind=engine)  # Clear previous data before tests
    Base.metadata.create_all(bind=engine)  # Create tables

    session = TestingSessionLocal()
    yield session  # Provide session to tests
    session.close()

    Base.metadata.drop_all(bind=engine)  # Cleanup after tests


@pytest.fixture(scope="session")
def override_get_db(db_session):
    """Dependency override to use test DB session in API"""

    def _get_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_db


@pytest.fixture(scope="module")
def client(override_get_db):
    """Provides a TestClient instance for API testing"""
    with TestClient(app) as c:
        yield c  # Test client is available for the test module
