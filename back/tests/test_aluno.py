import pytest


def test_create_aluno(db_session):
    """Test creating/getting aluno (public endpoint for login)"""
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
        response = client.post("/alunos/", json={
            "nome": "Aluno Novo",
            "email": "novo.aluno@gmail.com",
            "matricula": "2024001"
        })
        assert response.status_code == 201
        assert response.json()["nome"] == "Aluno Novo"
        assert response.json()["email"] == "novo.aluno@gmail.com"
        assert response.json()["matricula"] == "2024001"
        assert "id" in response.json()

    app.dependency_overrides.clear()


def test_create_aluno_returns_existing(db_session):
    """Test that creating aluno with existing email returns the existing one"""
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
        response1 = client.post("/alunos/", json={
            "nome": "Aluno Existente",
            "email": "existente.aluno@gmail.com",
            "matricula": "2024002"
        })
        assert response1.status_code == 201
        aluno_id = response1.json()["id"]

        response2 = client.post("/alunos/", json={
            "nome": "Outro Nome",
            "email": "existente.aluno@gmail.com",
            "matricula": "9999999"
        })
        assert response2.status_code == 201
        assert response2.json()["id"] == aluno_id  # Same ID
        assert response2.json()["nome"] == "Aluno Existente"  # Original name

    app.dependency_overrides.clear()


def test_get_my_profile(client_aluno):
    """Test getting current aluno's profile (authenticated)"""
    response = client_aluno.get("/alunos/me")
    assert response.status_code == 200
    assert response.json()["email"] == "aluno.teste@gmail.com"
    assert response.json()["nome"] == "Aluno Teste"


def test_update_my_profile(client_aluno):
    """Test updating current aluno's profile (authenticated)"""
    response = client_aluno.put("/alunos/me", json={
        "nome": "Aluno Atualizado",
        "email": "aluno.teste@gmail.com",
        "matricula": "999999"
    })
    assert response.status_code == 200
    assert response.json()["nome"] == "Aluno Atualizado"

    get_response = client_aluno.get("/alunos/me")
    assert get_response.json()["nome"] == "Aluno Atualizado"


def test_get_aluno_by_id(client_both):
    """Test getting aluno by ID (any authenticated user can access)"""
    from app.models.aluno_model import Aluno

    outro_aluno = Aluno(
        nome="Outro Aluno",
        email="outro@gmail.com",
        matricula="123456"
    )
    client_both.db.add(outro_aluno)
    client_both.db.commit()
    client_both.db.refresh(outro_aluno)
    aluno_id = outro_aluno.id

    with client_both.aluno() as client:
        response = client.get(f"/alunos/{aluno_id}")
        assert response.status_code == 200
        assert response.json()["nome"] == "Outro Aluno"
        assert response.json()["email"] == "outro@gmail.com"
        assert response.json()["matricula"] == "123456"

    with client_both.professor() as client:
        response = client.get(f"/alunos/{aluno_id}")
        assert response.status_code == 200
        assert response.json()["nome"] == "Outro Aluno"

    with client_both.aluno() as client:
        response = client.get("/alunos/99999")
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"].lower()
