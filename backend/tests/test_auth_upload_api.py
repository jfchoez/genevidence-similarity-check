from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import documents as documents_api
from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "AUTO_CREATE_TABLES", False)
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def noop_process_document(_: int) -> None:
        return None

    monkeypatch.setattr(settings, "STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setattr(documents_api, "process_document_task", noop_process_document)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_register_and_login(client: TestClient):
    register = client.post(
        "/auth/register",
        json={"email": "reviewer@example.com", "password": "strongpass123", "full_name": "Reviewer"},
    )
    assert register.status_code == 200
    assert register.json()["access_token"]

    login = client.post(
        "/auth/login",
        data={"username": "reviewer@example.com", "password": "strongpass123"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["email"] == "reviewer@example.com"


def test_document_upload_creates_record(client: TestClient):
    token = client.post(
        "/auth/register",
        json={"email": "uploader@example.com", "password": "strongpass123"},
    ).json()["access_token"]
    response = client.post(
        "/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "protocol.docx",
                b"simulated docx payload",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["original_filename"] == "protocol.docx"
    assert Path(settings.STORAGE_DIR).exists()
