import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

def create_prova_and_questao(client_professor, emails_permitidos, data_inicio, data_fim):
    """Creates a Prova and a Questao for testing."""
    prova_resp = client_professor.post("/provas/", json={
        "titulo": "Prova de Teste Submissao",
        "descricao": "Uma prova para testar submissoes",
        "data_aplicacao": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "professor_id": 1, # Mock professor has id=1
        "linguagem": "python",
        "emails_permitidos": emails_permitidos
    })
    assert prova_resp.status_code == 201
    prova_data = prova_resp.json()

    questao_resp = client_professor.post("/questoes/", json={
        "prova_id": prova_data["id"],
        "titulo": "Questão de Teste",
        "descricao": "Uma questão simples",
        "exemplo_input1": "1",
        "exemplo_output1": "1",
        "peso": 10.0
    })
    assert questao_resp.status_code == 201
    questao_data = questao_resp.json()
    
    return prova_data, questao_data

def test_create_submissao_success(client_professor, client_aluno):
    """A valid student submits code successfully within the time window and being on the whitelist."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)
    
    aluno_email = "aluno.teste@gmail.com"

    prova, questao = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)

    response = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "print('hello world')"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["prova_id"] == prova["id"]
    assert data["questao_id"] == questao["id"]
    assert data["codigo_submetido"] == "print('hello world')"
    assert data["aluno_id"] == 1 # Mock aluno has id=1


def test_update_submissao_on_second_post(client_professor, client_aluno):
    """Submitting a second time for the same question should update the existing submission."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)
    aluno_email = "aluno.teste@gmail.com"

    prova, questao = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)

    first_response = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "code v1"
    })
    assert first_response.status_code == 201
    first_sub_id = first_response.json()["id"]

    second_response = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "code v2"
    })
    assert second_response.status_code == 201
    second_sub_id = second_response.json()["id"]

    assert first_sub_id == second_sub_id # Must be the same DB record
    assert second_response.json()["codigo_submetido"] == "code v2"


def test_create_submissao_not_in_whitelist(client_professor, client_aluno):
    """A student not on the whitelist should be forbidden."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)

    prova, questao = create_prova_and_questao(client_professor, ["outro.aluno@gmail.com"], start_time, end_time)

    response = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "print('hello world')"
    })

    assert response.status_code == 403
    assert "não tem permissão" in response.json()["detail"]


def test_create_submissao_outside_time_window(client_professor, client_aluno):
    """A student submitting outside the time window should be forbidden."""
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(days=1)
    end_time = now + timedelta(days=2)
    aluno_email = "aluno.teste@gmail.com"

    prova, questao = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)

    response = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "print('hello world')"
    })

    assert response.status_code == 403
    assert "não está disponível" in response.json()["detail"]


def test_create_submissao_invalid_hierarchy(client_professor, client_aluno):
    """Submitting a question that doesn't belong to the test should be forbidden."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)
    aluno_email = "aluno.teste@gmail.com"

    prova1, questao1 = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)
    prova2, questao2 = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)

    response = client_aluno.post("/submissoes/", json={
        "prova_id": prova1["id"],
        "questao_id": questao2["id"], # Mismatched IDs
        "codigo_submetido": "print('wrong test')"
    })

    assert response.status_code == 403
    assert "não pertence à prova" in response.json()["detail"]

def test_create_submissao_unauthenticated():
    """An unauthenticated request should fail."""
    client = TestClient(pytest.importorskip("app.main").app) # Plain, unauthenticated client
    response = client.post("/submissoes/", json={
        "prova_id": 1,
        "questao_id": 1,
        "codigo_submetido": "code"
    })
    assert response.status_code == 403 # Should be Unauthorized

def test_create_submissao_prova_not_found(client_aluno):
    """Submitting to a non-existent prova_id should return 404."""
    response = client_aluno.post("/submissoes/", json={
        "prova_id": 999,
        "questao_id": 1,
        "codigo_submetido": "code"
    })
    assert response.status_code == 404
    assert "Prova não encontrada" in response.json()["detail"]


def test_cannot_submit_after_finalizing(client_professor, client_aluno):
    """After finalizing a test, student should not be able to submit more code."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)
    aluno_email = "aluno.teste@gmail.com"

    prova, questao = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)

    response = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "version 1"
    })
    assert response.status_code == 201

    finalize_response = client_aluno.post(f"/submissoes/finalizar/{prova['id']}", json=[{
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "final version"
    }])
    assert finalize_response.status_code == 200

    blocked_response = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "trying to cheat"
    })
    assert blocked_response.status_code == 403
    assert "já foi finalizada" in blocked_response.json()["detail"].lower()


def test_cannot_finalize_after_deadline(client_professor, client_aluno):
    """Student should NOT be able to finalize test after deadline + tolerance."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=2)
    end_time = now - timedelta(minutes=10)
    aluno_email = "aluno.teste@gmail.com"

    prova, questao = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)

    response = client_aluno.post(f"/submissoes/finalizar/{prova['id']}", json=[{
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "late submission"
    }])

    assert response.status_code == 403
    assert "prazo" in response.json()["detail"].lower() or "expirou" in response.json()["detail"].lower()


def test_can_finalize_within_tolerance(client_professor, client_aluno):
    """Student CAN finalize within 5 minute tolerance after deadline."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=2)
    end_time = now - timedelta(minutes=3)
    aluno_email = "aluno.teste@gmail.com"

    prova, questao = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)

    response = client_aluno.post(f"/submissoes/finalizar/{prova['id']}", json=[{
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "just in time"
    }])

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["finalizada"] == True


def test_cannot_finalize_twice(client_professor, client_aluno):
    """Student cannot finalize the same test twice."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)
    aluno_email = "aluno.teste@gmail.com"

    prova, questao = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)

    first_response = client_aluno.post(f"/submissoes/finalizar/{prova['id']}", json=[{
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "final answer"
    }])
    assert first_response.status_code == 200

    second_response = client_aluno.post(f"/submissoes/finalizar/{prova['id']}", json=[{
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "trying to change answer"
    }])
    assert second_response.status_code == 403
    assert "já foi finalizada" in second_response.json()["detail"].lower()


def test_finalize_validates_question_belongs_to_test(client_professor, client_aluno):
    """Finalizing with a question that doesn't belong to the test should fail."""
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=1)
    aluno_email = "aluno.teste@gmail.com"

    prova1, questao1 = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)
    prova2, questao2 = create_prova_and_questao(client_professor, [aluno_email], start_time, end_time)

    response = client_aluno.post(f"/submissoes/finalizar/{prova1['id']}", json=[{
        "prova_id": prova1["id"],
        "questao_id": questao2["id"],  # Wrong question!
        "codigo_submetido": "code"
    }])

    assert response.status_code == 400
    assert "não pertence" in response.json()["detail"].lower() or "não encontrada" in response.json()["detail"].lower()
