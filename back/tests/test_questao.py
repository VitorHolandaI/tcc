import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

def create_test_prova(client, emails, start, end, title="Prova de Teste"):
    prova_resp = client.post("/provas/", json={
        "titulo": title,
        "descricao": "Desc",
        "data_aplicacao": start.isoformat(),
        "data_fim": end.isoformat(),
        "professor_id": 1, 
        "linguagem": "python",
        "emails_permitidos": emails
    })
    assert prova_resp.status_code == 201
    return prova_resp.json()

def test_create_questao(client_professor):
    """Test creating a questao (professor who owns the prova)"""
    prova_response = client_professor.post("/provas/", json={
        "titulo": "Prova Questao",
        "descricao": "Teste",
        "data_aplicacao": "2024-02-10T08:00:00",
        "data_fim": "2024-02-10T12:00:00",
        "professor_id": 1,
        "linguagem": "python",
        "emails_permitidos": []
    })
    prova_id = prova_response.json()["id"]

    response = client_professor.post("/questoes/", json={
        "prova_id": prova_id,
        "titulo": "Questão 1: Calcular quadrado",
        "descricao": "Crie uma função que retorne o quadrado de um número",
        "exemplo_input1": "5",
        "exemplo_output1": "25",
        "exemplo_input2": "10",
        "exemplo_output2": "100",
        "peso": 10.0
    })
    assert response.status_code == 201
    assert response.json()["titulo"] == "Questão 1: Calcular quadrado"
    assert response.json()["prova_id"] == prova_id
    assert response.json()["peso"] == 10.0
    assert "id" in response.json()


def test_get_questao_by_id(client_professor):
    """Test getting a questao by ID"""
    prova_response = client_professor.post("/provas/", json={
        "titulo": "Prova Questao 2",
        "descricao": "Teste",
        "data_aplicacao": "2024-02-15T08:00:00",
        "data_fim": "2024-02-15T12:00:00",
        "professor_id": 1,
        "linguagem": "Java",
        "emails_permitidos": []
    })
    prova_id = prova_response.json()["id"]

    create_response = client_professor.post("/questoes/", json={
        "prova_id": prova_id,
        "titulo": "Questão de Java",
        "descricao": "Implemente uma classe",
        "exemplo_input1": "Hello",
        "exemplo_output1": "HELLO",
        "peso": 5.0
    })
    questao_id = create_response.json()["id"]

    response = client_professor.get(f"/questoes/{questao_id}")
    assert response.status_code == 200
    assert response.json()["id"] == questao_id
    assert response.json()["titulo"] == "Questão de Java"


def test_get_questao_not_found(client_professor):
    """Test getting a non-existent questao"""
    response = client_professor.get("/questoes/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Questão não encontrada"


def test_prova_with_multiple_questoes(client_professor):
    """Test that a Prova can have multiple Questoes"""
    prova_response = client_professor.post("/provas/", json={
        "titulo": "Prova com 3 Questões",
        "descricao": "Teste completo de python",
        "data_aplicacao": "2024-03-01T08:00:00",
        "data_fim": "2024-03-01T12:00:00",
        "professor_id": 1,
        "linguagem": "python",
        "emails_permitidos": []
    })
    prova_id = prova_response.json()["id"]

    for i in range(3):
        client_professor.post("/questoes/", json={
            "prova_id": prova_id,
            "titulo": f"Questão {i+1}", "descricao": "Desc", "exemplo_input1": "1", "exemplo_output1": "1", "peso": 10.0
        })

    response = client_professor.get(f"/questoes/prova/{prova_id}")
    assert response.status_code == 200
    questoes = response.json()
    assert len(questoes) == 3


def test_list_questoes_by_prova_owner_success(client_professor):
    """Test listing questoes by prova ID as the owner professor."""
    now = datetime.now(timezone.utc)
    prova = create_test_prova(client_professor, [], now, now + timedelta(hours=1))

    client_professor.post("/questoes/", json={"prova_id": prova["id"], "titulo": "Q1", "descricao": "D1", "exemplo_input1": "1", "exemplo_output1": "1", "peso": 1})
    client_professor.post("/questoes/", json={"prova_id": prova["id"], "titulo": "Q2", "descricao": "D2", "exemplo_input1": "2", "exemplo_output1": "2", "peso": 2})

    response = client_professor.get(f"/questoes/prova/{prova['id']}")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_questao(client_professor):
    """Test updating a questao"""
    prova_response = client_professor.post("/provas/", json={
        "titulo": "Prova Update", "descricao": "Teste", "data_aplicacao": "2024-02-25T08:00:00",
        "data_fim": "2024-02-25T12:00:00", "professor_id": 1, "linguagem": "python", "emails_permitidos": []
    })
    prova_id = prova_response.json()["id"]

    create_response = client_professor.post("/questoes/", json={
        "prova_id": prova_id, "titulo": "Questão Original", "descricao": "Descrição original",
        "exemplo_input1": "3", "exemplo_output1": "9", "peso": 10.0
    })
    questao_id = create_response.json()["id"]

    update_response = client_professor.put(f"/questoes/{questao_id}", json={
        "prova_id": prova_id, "titulo": "Questão Atualizada", "descricao": "Descrição atualizada",
        "exemplo_input1": "4", "exemplo_output1": "16", "peso": 20.0
    })
    assert update_response.status_code == 200
    assert update_response.json()["titulo"] == "Questão Atualizada"


def test_delete_questao(client_professor):
    """Test deleting a questao"""
    prova_response = client_professor.post("/provas/", json={
        "titulo": "Prova Delete", "descricao": "Teste", "data_aplicacao": "2024-03-01T08:00:00",
        "data_fim": "2024-03-01T12:00:00", "professor_id": 1, "linguagem": "python", "emails_permitidos": []
    })
    prova_id = prova_response.json()["id"]

    create_response = client_professor.post("/questoes/", json={
        "prova_id": prova_id, "titulo": "Questão Delete", "descricao": "Para deletar", "exemplo_input1": "5", "exemplo_output1": "25", "peso": 10.0
    })
    questao_id = create_response.json()["id"]

    delete_response = client_professor.delete(f"/questoes/{questao_id}")
    assert delete_response.status_code == 204
    assert client_professor.get(f"/questoes/{questao_id}").status_code == 404


def test_delete_prova_cascades_to_questoes(client_professor):
    """Test that deleting a Prova also deletes its Questoes"""
    prova_response = client_professor.post("/provas/", json={
        "titulo": "Prova Cascade", "descricao": "Teste cascade", "data_aplicacao": "2024-03-05T08:00:00",
        "data_fim": "2024-03-05T12:00:00", "professor_id": 1, "linguagem": "python", "emails_permitidos": []
    })
    prova_id = prova_response.json()["id"]

    questao_response = client_professor.post("/questoes/", json={"prova_id": prova_id, "titulo": "Questão Cascade", "descricao": "Será deletada", "exemplo_input1": "1", "exemplo_output1": "1", "peso": 10.0})
    questao_id = questao_response.json()["id"]

    client_professor.delete(f"/provas/{prova_id}")
    assert client_professor.get(f"/questoes/{questao_id}").status_code == 404


def test_list_questoes_aluno_success(client_professor, client_aluno):
    """A whitelisted student inside the time window should see the questions."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)
    aluno_email = "aluno.teste@gmail.com"

    prova = create_test_prova(client_professor, [aluno_email], start_time, end_time)
    response = client_aluno.get(f"/questoes/prova/{prova['id']}")
    
    assert response.status_code == 200


def test_list_questoes_aluno_not_in_whitelist(client_professor, client_aluno):
    """A student not on the whitelist should be forbidden."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)
    
    prova = create_test_prova(client_professor, ["outro.email@gmail.com"], start_time, end_time)
    response = client_aluno.get(f"/questoes/prova/{prova['id']}")
    
    assert response.status_code == 403
    assert "não tem permissão" in response.json()["detail"]


def test_list_questoes_aluno_outside_time_window(client_professor, client_aluno):
    """A student outside the time window should be forbidden."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=2)
    end_time = now - timedelta(days=1)
    aluno_email = "aluno.teste@gmail.com"
    
    prova = create_test_prova(client_professor, [aluno_email], start_time, end_time)
    response = client_aluno.get(f"/questoes/prova/{prova['id']}")
    
    assert response.status_code == 403
    assert "não está disponível" in response.json()["detail"]


def test_list_questoes_unauthenticated():
    """An unauthenticated user cannot list questions."""
    client = TestClient(pytest.importorskip("app.main").app)
    response = client.get("/questoes/prova/1")
    assert response.status_code == 403
