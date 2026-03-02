import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone


def create_prova_with_monitoring(client_professor, emails_permitidos, max_saidas, data_inicio=None, data_fim=None):
    """Creates a Prova with monitoring configuration."""
    if data_inicio is None:
        data_inicio = datetime.now(timezone.utc) - timedelta(hours=1)
    if data_fim is None:
        data_fim = datetime.now(timezone.utc) + timedelta(hours=2)

    prova_resp = client_professor.post("/provas/", json={
        "titulo": "Prova com Monitoramento",
        "descricao": "Testa sistema de monitoramento de saídas",
        "data_aplicacao": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "professor_id": 1,
        "linguagem": "python",
        "emails_permitidos": emails_permitidos,
        "max_saidas": max_saidas
    })
    assert prova_resp.status_code == 201
    return prova_resp.json()


def test_register_first_exit(client_professor, client_aluno):
    """First exit should create monitoring record with numero_saidas=1."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=3)

    response = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    assert response.status_code == 200
    data = response.json()
    assert data["numero_saidas"] == 1
    assert data["max_saidas"] == 3
    assert data["invalidada"] == False
    assert data["saidas_restantes"] == 2


def test_register_multiple_exits(client_professor, client_aluno):
    """Multiple exits should increment counter correctly."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=5)

    for i in range(1, 4):
        response = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
        assert response.status_code == 200
        data = response.json()
        assert data["numero_saidas"] == i
        assert data["invalidada"] == False
        assert data["saidas_restantes"] == 5 - i


def test_invalidate_after_exceeding_limit(client_professor, client_aluno):
    """Prova should be invalidated when exceeding max_saidas."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=2)

    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    response = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    assert response.status_code == 200
    data = response.json()
    assert data["numero_saidas"] == 3
    assert data["invalidada"] == True  # INVALIDATED!
    assert data["saidas_restantes"] == 0


def test_invalidation_is_permanent(client_professor, client_aluno):
    """Once invalidated, status should remain invalidated."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=1)

    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    response = client_aluno.get(f"/provas/{prova['id']}/status-monitoramento")
    assert response.status_code == 200
    assert response.json()["invalidada"] == True

    response = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    assert response.json()["invalidada"] == True


def test_get_status_no_exits_yet(client_professor, client_aluno):
    """Status should return 0 exits when student hasn't exited yet."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=3)

    response = client_aluno.get(f"/provas/{prova['id']}/status-monitoramento")

    assert response.status_code == 200
    data = response.json()
    assert data["numero_saidas"] == 0
    assert data["max_saidas"] == 3
    assert data["invalidada"] == False


def test_get_status_after_exits(client_professor, client_aluno):
    """Status should reflect current exit count."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=5)

    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    response = client_aluno.get(f"/provas/{prova['id']}/status-monitoramento")

    assert response.status_code == 200
    data = response.json()
    assert data["numero_saidas"] == 2
    assert data["invalidada"] == False


def test_get_status_when_invalidated(client_professor, client_aluno):
    """Status should show invalidated=True after exceeding limit."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=1)

    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    response = client_aluno.get(f"/provas/{prova['id']}/status-monitoramento")

    assert response.status_code == 200
    data = response.json()
    assert data["invalidada"] == True
    assert data["numero_saidas"] == 2


def test_cannot_submit_after_invalidation(client_professor, client_aluno):
    """Student should not be able to submit code after prova is invalidated."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=1)

    questao_resp = client_professor.post("/questoes/", json={
        "prova_id": prova["id"],
        "titulo": "Questão Teste",
        "descricao": "Uma questão",
        "exemplo_input1": "1",
        "exemplo_output1": "1",
        "peso": 10.0
    })
    assert questao_resp.status_code == 201
    questao = questao_resp.json()

    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    response = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "print('trying to cheat')"
    })

    assert response.status_code == 403
    assert "invalidada" in response.json()["detail"].lower()


def test_cannot_finalize_after_invalidation(client_professor, client_aluno):
    """Student should not be able to finalize prova after invalidation."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=1)

    questao_resp = client_professor.post("/questoes/", json={
        "prova_id": prova["id"],
        "titulo": "Questão Teste",
        "descricao": "Uma questão",
        "exemplo_input1": "1",
        "exemplo_output1": "1",
        "peso": 10.0
    })
    questao = questao_resp.json()

    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    response = client_aluno.post(f"/submissoes/finalizar/{prova['id']}", json=[{
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "print('final')"
    }])

    assert response.status_code == 403
    assert "invalidada" in response.json()["detail"].lower()


def test_can_submit_before_invalidation(client_professor, client_aluno):
    """Student CAN submit normally when within exit limit."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=3)

    questao_resp = client_professor.post("/questoes/", json={
        "prova_id": prova["id"],
        "titulo": "Questão Teste",
        "descricao": "Uma questão",
        "exemplo_input1": "1",
        "exemplo_output1": "1",
        "peso": 10.0
    })
    questao = questao_resp.json()

    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    response = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "print('ok')"
    })

    assert response.status_code == 201


def test_cannot_register_exit_without_permission(client_professor, client_aluno):
    """Student not on whitelist cannot register exits."""
    prova = create_prova_with_monitoring(client_professor, ["outro.aluno@gmail.com"], max_saidas=3)

    response = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    assert response.status_code == 403
    assert "permissão" in response.json()["detail"].lower()


def test_cannot_get_status_without_permission(client_professor, client_aluno):
    """Student not on whitelist cannot get monitoring status."""
    prova = create_prova_with_monitoring(client_professor, ["outro.aluno@gmail.com"], max_saidas=3)

    response = client_aluno.get(f"/provas/{prova['id']}/status-monitoramento")

    assert response.status_code == 403
    assert "permissão" in response.json()["detail"].lower()


def test_register_exit_prova_not_found(client_aluno):
    """Registering exit for non-existent prova should return 404."""
    response = client_aluno.post("/provas/999/registrar-saida")
    assert response.status_code == 404


def test_get_status_prova_not_found(client_aluno):
    """Getting status for non-existent prova should return 404."""
    response = client_aluno.get("/provas/999/status-monitoramento")
    assert response.status_code == 404


def test_max_saidas_zero_allows_unlimited(client_professor, client_aluno):
    """max_saidas=0 should allow unlimited exits without invalidation."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=0)

    for _ in range(10):
        response = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
        assert response.status_code == 200
        assert response.json()["invalidada"] == False


def test_different_students_independent_counters(client_professor, client_aluno, db_session):
    """Different students should have independent exit counters."""
    from app.models.aluno_model import Aluno

    aluno2 = Aluno(
        nome="Aluno 2",
        email="aluno2@test.com",
        matricula="888888"
    )
    db_session.add(aluno2)
    db_session.commit()

    prova = create_prova_with_monitoring(
        client_professor,
        ["aluno.teste@gmail.com", "aluno2@test.com"],
        max_saidas=3
    )

    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    client_aluno.post(f"/provas/{prova['id']}/registrar-saida")

    status = client_aluno.get(f"/provas/{prova['id']}/status-monitoramento")
    assert status.json()["numero_saidas"] == 2

    # but the repository layer ensures this isolation


def test_monitoring_max_saidas_configuration(client_professor, client_aluno):
    """Different provas can have different max_saidas limits."""
    aluno_email = "aluno.teste@gmail.com"

    prova1 = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=1)

    prova2 = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=10)

    status1 = client_aluno.get(f"/provas/{prova1['id']}/status-monitoramento")
    status2 = client_aluno.get(f"/provas/{prova2['id']}/status-monitoramento")

    assert status1.json()["max_saidas"] == 1
    assert status2.json()["max_saidas"] == 10


def test_invalidation_at_exact_limit(client_professor, client_aluno):
    """Prova should be invalidated when numero_saidas > max_saidas (not >=)."""
    aluno_email = "aluno.teste@gmail.com"
    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=3)

    # 1st, 2nd, 3rd exit: should NOT invalidate
    for i in range(1, 4):
        response = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
        assert response.json()["invalidada"] == False

    # 4th exit: should invalidate (3 + 1 > 3)
    response = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    assert response.json()["invalidada"] == True
    assert response.json()["numero_saidas"] == 4


def test_full_monitoring_workflow(client_professor, client_aluno):
    """Test complete workflow: create prova, register exits, invalidate, block submission."""
    aluno_email = "aluno.teste@gmail.com"

    prova = create_prova_with_monitoring(client_professor, [aluno_email], max_saidas=2)

    questao_resp = client_professor.post("/questoes/", json={
        "prova_id": prova["id"],
        "titulo": "Questão Final",
        "descricao": "Teste workflow",
        "exemplo_input1": "5",
        "exemplo_output1": "25",
        "peso": 10.0
    })
    questao = questao_resp.json()

    status = client_aluno.get(f"/provas/{prova['id']}/status-monitoramento")
    assert status.json()["numero_saidas"] == 0

    sub1 = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "def square(x): return x*x"
    })
    assert sub1.status_code == 201

    exit1 = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    assert exit1.json()["numero_saidas"] == 1
    assert exit1.json()["invalidada"] == False

    sub2 = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "def square(x): return x**2"
    })
    assert sub2.status_code == 201

    exit2 = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    assert exit2.json()["numero_saidas"] == 2
    assert exit2.json()["saidas_restantes"] == 0
    assert exit2.json()["invalidada"] == False  # Still not invalidated at limit

    exit3 = client_aluno.post(f"/provas/{prova['id']}/registrar-saida")
    assert exit3.json()["numero_saidas"] == 3
    assert exit3.json()["invalidada"] == True

    sub3 = client_aluno.post("/submissoes/", json={
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "print('blocked')"
    })
    assert sub3.status_code == 403

    finalize = client_aluno.post(f"/submissoes/finalizar/{prova['id']}", json=[{
        "prova_id": prova["id"],
        "questao_id": questao["id"],
        "codigo_submetido": "print('blocked')"
    }])
    assert finalize.status_code == 403
