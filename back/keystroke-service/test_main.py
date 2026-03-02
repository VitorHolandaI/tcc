"""
Tests for Keystroke Analysis Service endpoints.

Uses mocked Firebase auth and mocked main database to test
the API endpoints without external dependencies.
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_keystroke_service.db"

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import firebase_admin
firebase_admin._apps = {"default": True}

from database import Base as ServiceBase, KeystrokeAnalysis, get_db
from main import app, verify_jwt_token

TEST_DB_URL = "sqlite:///./test_keystroke_service.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


MOCK_PROFESSOR = {
    "uid": "prof-uid-123",
    "email": "professor.teste@ccc.ufcg.edu.br",
    "user_type": "professor"
}

MOCK_STUDENT = {
    "uid": "aluno-uid-123",
    "email": "aluno.teste@gmail.com",
    "user_type": "aluno"
}


async def mock_verify_professor(authorization: str = None):
    return MOCK_PROFESSOR


async def mock_verify_student(authorization: str = None):
    return MOCK_STUDENT


@pytest.fixture(scope="function")
def service_db():
    """Create fresh service database for each test."""
    ServiceBase.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        ServiceBase.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client_professor(service_db):
    def override_db():
        try:
            yield service_db
        finally:
            pass

    app.dependency_overrides[verify_jwt_token] = mock_verify_professor
    app.dependency_overrides[get_db] = override_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client_student(service_db):
    def override_db():
        try:
            yield service_db
        finally:
            pass

    app.dependency_overrides[verify_jwt_token] = mock_verify_student
    app.dependency_overrides[get_db] = override_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_health_check(client_professor):
    """Health check endpoint returns service info."""
    response = client_professor.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Keystroke Analysis Service"
    assert data["status"] == "running"



def test_get_analysis_not_found(client_professor):
    """Returns not_found when no analysis exists."""
    response = client_professor.get("/analysis/1/1")
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"


def test_get_analysis_processing(client_professor, service_db):
    """Returns processing status when analysis is in progress."""
    analysis = KeystrokeAnalysis(
        prova_id=1, aluno_id=1, status="processing"
    )
    service_db.add(analysis)
    service_db.commit()

    response = client_professor.get("/analysis/1/1")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"


def test_get_analysis_failed(client_professor, service_db):
    """Returns failed status with error message."""
    analysis = KeystrokeAnalysis(
        prova_id=1, aluno_id=1, status="failed",
        error_message="Something went wrong"
    )
    service_db.add(analysis)
    service_db.commit()

    response = client_professor.get("/analysis/1/1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error"] == "Something went wrong"


def test_get_analysis_completed(client_professor, service_db):
    """Returns completed analysis with all metrics."""
    analysis = KeystrokeAnalysis(
        prova_id=1, aluno_id=1, status="completed",
        total_events=500,
        hold_time_avg=0.12,
        hold_time_std=0.03,
        flight_time_avg=0.15,
        flight_time_std=0.05,
        command_counts={"paste": 3, "copy": 2},
        suspicious_percentage=5.0,
        total_commands=100,
        avg_manhattan_distance=2.5,
        command_sequences=8,
        completed_at=datetime(2024, 6, 15, 14, 30, 0)
    )
    service_db.add(analysis)
    service_db.commit()

    response = client_professor.get("/analysis/1/1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["prova_id"] == 1
    assert data["aluno_id"] == 1
    assert data["typing_metrics"]["total_events"] == 500
    assert data["typing_metrics"]["hold_time_avg"] == 0.12
    assert data["typing_metrics"]["flight_time_avg"] == 0.15
    assert data["suspicious_commands"]["suspicious_percentage"] == 5.0
    assert data["suspicious_commands"]["command_counts"]["paste"] == 3
    assert data["completed_at"] is not None


def test_get_analysis_student_blocked(client_student):
    """Students cannot access keystroke analysis."""
    response = client_student.get("/analysis/1/1")
    assert response.status_code == 403



def test_start_analysis_student_blocked(client_student):
    """Students cannot start keystroke analysis."""
    response = client_student.post("/analyze/1/1")
    assert response.status_code == 403


@patch("main.MainSessionLocal")
def test_start_analysis_no_submissao(mock_main_db_class, client_professor):
    """Returns 404 when no submissao exists."""
    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.return_value = None
    mock_main_db_class.return_value = mock_main_db

    response = client_professor.post("/analyze/1/1")
    assert response.status_code == 404


@patch("main.MainSessionLocal")
def test_start_analysis_no_keystroke_data(mock_main_db_class, client_professor):
    """Returns 404 when submissao has no keystroke data."""
    mock_submissao = MagicMock()
    mock_submissao.keystroke_dynamics = None

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.return_value = mock_submissao
    mock_main_db_class.return_value = mock_main_db

    response = client_professor.post("/analyze/1/1")
    assert response.status_code == 404


@patch("main.MainSessionLocal")
def test_start_analysis_already_completed(mock_main_db_class, client_professor, service_db):
    """Returns completed status if analysis already exists."""
    analysis = KeystrokeAnalysis(
        prova_id=1, aluno_id=1, status="completed"
    )
    service_db.add(analysis)
    service_db.commit()

    mock_submissao = MagicMock()
    mock_submissao.keystroke_dynamics = [{"key": "a"}]

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.return_value = mock_submissao
    mock_main_db_class.return_value = mock_main_db

    response = client_professor.post("/analyze/1/1")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@patch("main.MainSessionLocal")
def test_start_analysis_success(mock_main_db_class, client_professor, service_db):
    """Successfully starts keystroke analysis in background."""
    mock_submissao = MagicMock()
    mock_submissao.keystroke_dynamics = [
        {"key": "a", "timestamp": "2024-01-01 12:00:00.000", "hold_time": 0.05, "flight_time": 0.1}
    ]

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.return_value = mock_submissao
    mock_main_db_class.return_value = mock_main_db

    response = client_professor.post("/analyze/1/1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["total_events"] == 1
