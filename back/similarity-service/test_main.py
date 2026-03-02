"""
Tests for Code Similarity Analysis Service endpoints.

Uses mocked Firebase auth and mocked main database to test
the API endpoints without external dependencies.
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///./test_similarity_service.db"

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import firebase_admin
firebase_admin._apps = {"default": True}

from database import Base as ServiceBase, SimilarityAnalysis, get_db
from main import app, verify_jwt_token

TEST_DB_URL = "sqlite:///./test_similarity_service.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


MOCK_PROFESSOR = {
    "uid": "prof-uid-123",
    "email": "professor.teste@ccc.ufcg.edu.br",
    "user_type": "professor"
}


async def mock_verify_professor(authorization: str = None):
    return MOCK_PROFESSOR


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


def test_health_check(client_professor):
    """Health check returns service info."""
    response = client_professor.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Code Similarity Analysis Service"
    assert data["status"] == "running"



@patch("main.MainSessionLocal")
def test_get_analysis_not_found(mock_main_db_class, client_professor):
    """Returns not_found when no analysis exists."""
    mock_professor = MagicMock()
    mock_professor.id = 1
    mock_prova = MagicMock()
    mock_prova.professor_id = 1

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.side_effect = [
        mock_professor, mock_prova
    ]
    mock_main_db_class.return_value = mock_main_db

    response = client_professor.get("/analysis/1")
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"


@patch("main.MainSessionLocal")
def test_get_analysis_processing(mock_main_db_class, client_professor, service_db):
    """Returns processing status when analysis is in progress."""
    mock_professor = MagicMock()
    mock_professor.id = 1
    mock_prova = MagicMock()
    mock_prova.professor_id = 1

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.side_effect = [
        mock_professor, mock_prova
    ]
    mock_main_db_class.return_value = mock_main_db

    analysis = SimilarityAnalysis(prova_id=1, status="processing")
    service_db.add(analysis)
    service_db.commit()

    response = client_professor.get("/analysis/1")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"


@patch("main.MainSessionLocal")
def test_get_analysis_failed(mock_main_db_class, client_professor, service_db):
    """Returns failed status with error message."""
    mock_professor = MagicMock()
    mock_professor.id = 1
    mock_prova = MagicMock()
    mock_prova.professor_id = 1

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.side_effect = [
        mock_professor, mock_prova
    ]
    mock_main_db_class.return_value = mock_main_db

    analysis = SimilarityAnalysis(
        prova_id=1, status="failed",
        error_message="Analysis error"
    )
    service_db.add(analysis)
    service_db.commit()

    response = client_professor.get("/analysis/1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert data["error"] == "Analysis error"


@patch("main.MainSessionLocal")
def test_get_analysis_completed(mock_main_db_class, client_professor, service_db):
    """Returns completed analysis with full results."""
    mock_professor = MagicMock()
    mock_professor.id = 1
    mock_prova = MagicMock()
    mock_prova.professor_id = 1

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.side_effect = [
        mock_professor, mock_prova
    ]
    mock_main_db_class.return_value = mock_main_db

    analysis = SimilarityAnalysis(
        prova_id=1, status="completed",
        total_students=3,
        total_flagged_pairs=1,
        threshold_used=70.0,
        results=[{
            "questao_id": 1,
            "questao_titulo": "Q1",
            "total_pairs": 3,
            "flagged_pairs": 1,
            "pairs": [{
                "aluno_a": {"id": 1, "nome": "A", "email": "a@g.com"},
                "aluno_b": {"id": 2, "nome": "B", "email": "b@g.com"},
                "text_similarity": 95.0,
                "normalized_similarity": 100.0,
                "max_similarity": 100.0,
                "flagged": True
            }]
        }],
        completed_at=datetime(2024, 6, 15, 14, 30, 0)
    )
    service_db.add(analysis)
    service_db.commit()

    response = client_professor.get("/analysis/1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["total_students"] == 3
    assert data["total_flagged_pairs"] == 1
    assert data["threshold_used"] == 70.0
    assert len(data["questions"]) == 1
    assert data["questions"][0]["pairs"][0]["max_similarity"] == 100.0
    assert data["completed_at"] is not None


@patch("main.MainSessionLocal")
def test_get_analysis_not_owner(mock_main_db_class, client_professor):
    """Professor who doesn't own the prova gets 403."""
    mock_professor = MagicMock()
    mock_professor.id = 1
    mock_prova = MagicMock()
    mock_prova.professor_id = 999

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.side_effect = [
        mock_professor, mock_prova
    ]
    mock_main_db_class.return_value = mock_main_db

    response = client_professor.get("/analysis/1")
    assert response.status_code == 403



@patch("main.MainSessionLocal")
def test_start_analysis_not_owner(mock_main_db_class, client_professor):
    """Professor who doesn't own the prova cannot start analysis."""
    mock_professor = MagicMock()
    mock_professor.id = 1
    mock_prova = MagicMock()
    mock_prova.professor_id = 999

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.side_effect = [
        mock_professor, mock_prova
    ]
    mock_main_db_class.return_value = mock_main_db

    response = client_professor.post("/analyze/1")
    assert response.status_code == 403


@patch("main.MainSessionLocal")
def test_start_analysis_already_processing(mock_main_db_class, client_professor, service_db):
    """Returns processing status if analysis is already running."""
    analysis = SimilarityAnalysis(prova_id=1, status="processing")
    service_db.add(analysis)
    service_db.commit()

    mock_professor = MagicMock()
    mock_professor.id = 1
    mock_prova = MagicMock()
    mock_prova.id = 1
    mock_prova.professor_id = 1
    mock_prova.linguagem = "python"

    mock_submissao = MagicMock()
    mock_submissao.prova_id = 1
    mock_submissao.aluno_id = 1
    mock_submissao.questao_id = 1
    mock_submissao.codigo_submetido = "print('hello')"

    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.side_effect = [
        mock_professor, mock_prova, mock_prova
    ]
    mock_main_db.query.return_value.filter.return_value.all.side_effect = [
        [mock_submissao], []
    ]
    mock_main_db_class.return_value = mock_main_db

    response = client_professor.post("/analyze/1")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"
