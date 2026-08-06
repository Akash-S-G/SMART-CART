import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_readyz():
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

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
    # Attempt 6 consecutive failed logins to trigger lockout
    bad_payload = {"email": "lockout_test@example.com", "password": "wrongpassword123"}
    for i in range(5):
        client.post("/auth/login", json=bad_payload)
    
    # 6th attempt must return 429 Too Many Requests
    response = client.post("/auth/login", json=bad_payload)
    assert response.status_code == 429
    assert "locked" in response.json()["detail"].lower()
