"""
Pytest configuration and shared fixtures
"""
import os

# IMPORTANTE: Establecer modo test ANTES de importar app.main
os.environ["TESTING"] = "1"

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.config import settings

# Test database URL - usar SQLite en memoria para tests
TEST_DATABASE_URL = "sqlite:///./test.db"

# Crear engine de prueba
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    Rollback all changes after the test.
    """
    # Crear todas las tablas
    Base.metadata.create_all(bind=test_engine)
    
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        # Limpiar todas las tablas después del test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a TestClient with database override
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def async_client(db_session: Session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an AsyncClient for concurrent tests
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@upao.edu.pe",
        "password": "TestPassword123",
        "nombre": "Test",
        "apellido": "User",
        "codigo": "T12345678"
    }


@pytest.fixture
def test_admin_data():
    """Sample admin user data for testing"""
    return {
        "email": "admin@upao.edu.pe",
        "password": "AdminPassword123",
        "nombre": "Admin",
        "apellido": "Test",
        "codigo": "A12345678",
        "is_admin": True
    }


@pytest.fixture
def auth_headers(client: TestClient, test_user_data: dict) -> dict:
    """
    Create a user and return authentication headers
    """
    # Registrar usuario
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 201
    
    # Login
    login_data = {
        "username": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client: TestClient, db_session: Session, test_admin_data: dict) -> dict:
    """
    Create an admin user and return authentication headers
    """
    from app.models import Usuario
    from app.utils.security import get_password_hash
    
    # Crear admin directamente en la DB
    hashed_password = get_password_hash(test_admin_data["password"])
    admin = Usuario(
        email=test_admin_data["email"],
        password_hash=hashed_password,
        nombre=test_admin_data["nombre"],
        apellido=test_admin_data["apellido"],
        codigo=test_admin_data["codigo"],
        is_admin=True,
        firebase_uid="test-admin-uid"
    )
    db_session.add(admin)
    db_session.commit()
    
    # Login
    login_data = {
        "username": test_admin_data["email"],
        "password": test_admin_data["password"]
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_malla_data():
    """Sample malla data for testing"""
    return {
        "codigo": "ING-SOFT-2024",
        "nombre": "Ingeniería de Software",
        "anio": 2024,
        "ciclos_totales": 10
    }


@pytest.fixture
def sample_curso_data():
    """Sample curso data for testing"""
    return {
        "codigo": "CURSO-001",
        "nombre": "Introducción a la Programación",
        "creditos": 4,
        "ciclo": 1,
        "tipo": "obligatorio"
    }
