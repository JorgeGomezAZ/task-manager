"""
Integration tests for the Task Manager API.
Uses an in-memory SQLite database so tests stay isolated even though the app defaults to PostgreSQL.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, get_engine_kwargs
from app.main import app

# ── In-memory test database ────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    **get_engine_kwargs(TEST_DATABASE_URL),
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Helpers ────────────────────────────────────────────────────────────────────

def register_and_login(client: TestClient, email: str = "user@test.com", password: str = "pass123"):
    client.post("/auth/register", json={"email": email, "password": password})
    r = client.post("/auth/login", data={"username": email, "password": password})
    token = r.json()["access_token"]
    return {"Authorization": "Bearer " + token}


# ── Auth tests ─────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        r = client.post("/auth/register", json={"email": "new@test.com", "password": "pass123"})
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "new@test.com"
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client):
        client.post("/auth/register", json={"email": "dup@test.com", "password": "pass123"})
        r = client.post("/auth/register", json={"email": "dup@test.com", "password": "other"})
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"]

    def test_login_success(self, client):
        client.post("/auth/register", json={"email": "login@test.com", "password": "pass123"})
        r = client.post("/auth/login", data={"username": "login@test.com", "password": "pass123"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/auth/register", json={"email": "a@test.com", "password": "correct"})
        r = client.post("/auth/login", data={"username": "a@test.com", "password": "wrong"})
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        r = client.post("/auth/login", data={"username": "nobody@test.com", "password": "x"})
        assert r.status_code == 401


# ── Task tests ─────────────────────────────────────────────────────────────────

class TestTasks:
    def test_create_task(self, client):
        headers = register_and_login(client)
        r = client.post("/tasks/", json={"title": "Buy milk"}, headers=headers)
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Buy milk"
        assert data["completed"] is False

    def test_list_tasks(self, client):
        headers = register_and_login(client)
        client.post("/tasks/", json={"title": "Task A"}, headers=headers)
        client.post("/tasks/", json={"title": "Task B"}, headers=headers)
        r = client.get("/tasks/", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_tasks_scoped_to_user(self, client):
        h1 = register_and_login(client, "alice@test.com", "pass")
        h2 = register_and_login(client, "bob@test.com", "pass")
        client.post("/tasks/", json={"title": "Alice task"}, headers=h1)
        r = client.get("/tasks/", headers=h2)
        assert r.status_code == 200
        assert len(r.json()) == 0

    def test_update_task(self, client):
        headers = register_and_login(client)
        task_id = client.post("/tasks/", json={"title": "Old"}, headers=headers).json()["id"]
        r = client.put(f"/tasks/{task_id}", json={"title": "New", "completed": True}, headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "New"
        assert data["completed"] is True

    def test_update_other_users_task_returns_404(self, client):
        h1 = register_and_login(client, "alice@test.com", "pass")
        h2 = register_and_login(client, "bob@test.com", "pass")
        task_id = client.post("/tasks/", json={"title": "Alice task"}, headers=h1).json()["id"]
        r = client.put(f"/tasks/{task_id}", json={"completed": True}, headers=h2)
        assert r.status_code == 404

    def test_delete_task(self, client):
        headers = register_and_login(client)
        task_id = client.post("/tasks/", json={"title": "Delete me"}, headers=headers).json()["id"]
        r = client.delete(f"/tasks/{task_id}", headers=headers)
        assert r.status_code == 204
        r = client.get("/tasks/", headers=headers)
        assert len(r.json()) == 0

    def test_delete_other_users_task_returns_404(self, client):
        h1 = register_and_login(client, "alice@test.com", "pass")
        h2 = register_and_login(client, "bob@test.com", "pass")
        task_id = client.post("/tasks/", json={"title": "Alice task"}, headers=h1).json()["id"]
        r = client.delete(f"/tasks/{task_id}", headers=h2)
        assert r.status_code == 404

    def test_unauthenticated_get_tasks(self, client):
        r = client.get("/tasks/")
        assert r.status_code == 401

    def test_unauthenticated_create_task(self, client):
        r = client.post("/tasks/", json={"title": "Sneaky"})
        assert r.status_code == 401
