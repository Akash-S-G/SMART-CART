import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

# Map PostgreSQL JSONB to SQLite JSON for test suite
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Create in-memory SQLite database with StaticPool so all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
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

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_readyz():
    response = client.get("/readyz")
    assert response.status_code == 200

def test_list_products():
    response = client.get("/products?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_list_categories():
    response = client.get("/products/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_login_brute_force_lockout():
    bad_payload = {"email": "lockout_test@example.com", "password": "wrongpassword123"}
    for i in range(5):
        client.post("/auth/login", json=bad_payload)
    
    response = client.post("/auth/login", json=bad_payload)
    assert response.status_code == 429
    assert "locked" in response.json()["detail"].lower()
