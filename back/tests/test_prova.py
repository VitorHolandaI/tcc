import pytest


def test_create_prova(client_professor):
    """Test creating a prova (professor only)"""
    response = client_professor.post("/provas/", json={
        "titulo": "Prova de Python",
        "descricao": "Teste de programação básica",
        "data_aplicacao": "2024-02-10T08:00:00",
        "data_fim": "2024-02-10T12:00:00",
        "professor_id": 1,  # Will be overridden by auth
        "linguagem": "Python",
        "emails_permitidos": ["aluno.teste@gmail.com"]
    })
    assert response.status_code == 201
    assert response.json()["titulo"] == "Prova de Python"
    assert response.json()["linguagem"] == "python"
    assert "id" in response.json()


def test_get_prova_by_id(client_professor):
    """Test getting a prova by ID (owner professor)"""
    create_response = client_professor.post("/provas/", json={
        "titulo": "Prova de Java",
        "descricao": "Teste de OOP",
        "data_aplicacao": "2024-02-15T08:00:00",
        "data_fim": "2024-02-15T12:00:00",
        "professor_id": 1,
        "linguagem": "Java",
        "emails_permitidos": ["aluno.teste@gmail.com"]
    })
    prova_id = create_response.json()["id"]

    response = client_professor.get(f"/provas/{prova_id}")
    assert response.status_code == 200
    assert response.json()["id"] == prova_id
    assert response.json()["titulo"] == "Prova de Java"


def test_get_prova_not_found(client_professor):
    """Test getting a non-existent prova"""
    response = client_professor.get("/provas/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Prova não encontrada"


def test_list_my_provas_todas(client_professor):
    """Test listing all provas for authenticated professor"""
    client_professor.post("/provas/", json={
        "titulo": "Prova 1",
        "descricao": "Teste 1",
        "data_aplicacao": "2024-02-20T08:00:00",
        "data_fim": "2024-02-20T12:00:00",
        "professor_id": 1,
        "linguagem": "Python",
        "emails_permitidos": ["aluno1@test.com"]
    })
    client_professor.post("/provas/", json={
        "titulo": "Prova 2",
        "descricao": "Teste 2",
        "data_aplicacao": "2024-02-25T08:00:00",
        "data_fim": "2024-02-25T12:00:00",
        "professor_id": 1,
        "linguagem": "Java",
        "emails_permitidos": ["aluno2@test.com"]
    })

    response = client_professor.get("/provas/me/todas")
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_list_my_provas_agendadas(client_professor):
    """Test listing scheduled provas for authenticated professor"""
    client_professor.post("/provas/", json={
        "titulo": "Prova Futura",
        "descricao": "Prova agendada",
        "data_aplicacao": "2030-12-01T08:00:00",
        "data_fim": "2030-12-01T12:00:00",
        "professor_id": 1,
        "linguagem": "Python",
        "emails_permitidos": []
    })

    response = client_professor.get("/provas/me/agendadas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_my_provas_em_andamento(client_professor):
    """Test listing in-progress provas for authenticated professor"""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")
    now = datetime.now(SAO_PAULO_TZ)

    client_professor.post("/provas/", json={
        "titulo": "Prova Em Andamento",
        "descricao": "Prova acontecendo agora",
        "data_aplicacao": (now - timedelta(hours=1)).isoformat(),
        "data_fim": (now + timedelta(hours=2)).isoformat(),
        "professor_id": 1,
        "linguagem": "Python",
        "emails_permitidos": []
    })

    response = client_professor.get("/provas/me/em-andamento")
    assert response.status_code == 200
    provas = response.json()
    assert isinstance(provas, list)
    titles = [p["titulo"] for p in provas]
    assert "Prova Em Andamento" in titles


def test_list_my_provas_passadas(client_professor):
    """Test listing past provas for authenticated professor"""
    client_professor.post("/provas/", json={
        "titulo": "Prova Passada",
        "descricao": "Prova antiga",
        "data_aplicacao": "2020-01-01T08:00:00",
        "data_fim": "2020-01-01T12:00:00",
        "professor_id": 1,
        "linguagem": "Python",
        "emails_permitidos": []
    })

    response = client_professor.get("/provas/me/passadas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_prova(client_professor):
    """Test updating a prova (owner professor only)"""
    create_response = client_professor.post("/provas/", json={
        "titulo": "Prova Original",
        "descricao": "Descrição original",
        "data_aplicacao": "2024-03-01T08:00:00",
        "data_fim": "2024-03-01T12:00:00",
        "professor_id": 1,
        "linguagem": "Python",
        "emails_permitidos": ["aluno@test.com"]
    })
    prova_id = create_response.json()["id"]

    update_response = client_professor.put(f"/provas/{prova_id}", json={
        "titulo": "Prova Atualizada",
        "descricao": "Descrição atualizada",
        "data_aplicacao": "2024-03-05T08:00:00",
        "data_fim": "2024-03-05T12:00:00",
        "professor_id": 1,
        "linguagem": "Java",
        "emails_permitidos": ["aluno@test.com", "aluno2@test.com"]
    })
    assert update_response.status_code == 200
    assert update_response.json()["titulo"] == "Prova Atualizada"
    assert update_response.json()["linguagem"] == "java"


def test_delete_prova(client_professor):
    """Test deleting a prova (owner professor only)"""
    create_response = client_professor.post("/provas/", json={
        "titulo": "Prova Delete",
        "descricao": "Para deletar",
        "data_aplicacao": "2024-03-10T08:00:00",
        "data_fim": "2024-03-10T12:00:00",
        "professor_id": 1,
        "linguagem": "Python",
        "emails_permitidos": []
    })
    prova_id = create_response.json()["id"]

    delete_response = client_professor.delete(f"/provas/{prova_id}")
    assert delete_response.status_code == 204

    get_response = client_professor.get(f"/provas/{prova_id}")
    assert get_response.status_code == 404
