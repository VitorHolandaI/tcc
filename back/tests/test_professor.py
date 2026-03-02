import pytest


def test_create_professor(db_session):
    """Test creating/getting professor (public endpoint for login)"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        response = client.post("/professores/", json={
            "nome": "Professor Novo",
            "email": "novo@ccc.ufcg.edu.br"
        })
        assert response.status_code == 201
        assert response.json()["nome"] == "Professor Novo"
        assert response.json()["email"] == "novo@ccc.ufcg.edu.br"
        assert "id" in response.json()

    app.dependency_overrides.clear()


def test_create_professor_returns_existing(db_session):
    """Test that creating professor with existing email returns the existing one"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        response1 = client.post("/professores/", json={
            "nome": "Professor Existente",
            "email": "existente@ccc.ufcg.edu.br"
        })
        assert response1.status_code == 201
        professor_id = response1.json()["id"]

        response2 = client.post("/professores/", json={
            "nome": "Outro Nome",
            "email": "existente@ccc.ufcg.edu.br"
        })
        assert response2.status_code == 201
        assert response2.json()["id"] == professor_id  # Same ID
        assert response2.json()["nome"] == "Professor Existente"  # Original name

    app.dependency_overrides.clear()


def test_get_my_profile(client_professor):
    """Test getting current professor's profile (authenticated)"""
    response = client_professor.get("/professores/me")
    assert response.status_code == 200
    assert response.json()["email"] == "professor.teste@ccc.ufcg.edu.br"
    assert response.json()["nome"] == "Professor Teste"


def test_update_my_profile(client_professor):
    """Test updating current professor's profile (authenticated)"""
    response = client_professor.put("/professores/me", json={
        "nome": "Professor Atualizado",
        "email": "professor.teste@ccc.ufcg.edu.br"
    })
    assert response.status_code == 200
    assert response.json()["nome"] == "Professor Atualizado"

    get_response = client_professor.get("/professores/me")
    assert get_response.json()["nome"] == "Professor Atualizado"
