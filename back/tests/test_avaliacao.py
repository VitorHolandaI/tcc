import pytest


def _create_prova_with_questao_and_submissao(client_professor, db_session):
    """Helper: create a prova, add a questao, and manually insert a submissao."""
    prova_resp = client_professor.post("/provas/", json={
        "titulo": "Prova Avaliacao",
        "descricao": "Teste de avaliacao",
        "data_aplicacao": "2020-01-01T08:00:00",
        "data_fim": "2030-12-31T23:59:00",
        "professor_id": 1,
        "linguagem": "Python",
        "emails_permitidos": ["aluno.teste@gmail.com"]
    })
    assert prova_resp.status_code == 201
    prova_id = prova_resp.json()["id"]

    questao_resp = client_professor.post("/questoes/", json={
        "prova_id": prova_id,
        "titulo": "Hello World",
        "descricao": "Escreva hello world",
        "exemplo_input1": "",
        "exemplo_output1": "hello world",
        "peso": 10.0
    })
    assert questao_resp.status_code == 201
    questao_id = questao_resp.json()["id"]

    from app.models.submissao_model import Submissao
    from datetime import datetime
    sub = Submissao(
        aluno_id=1,
        prova_id=prova_id,
        questao_id=questao_id,
        codigo_submetido="print('hello world')",
        data_envio=datetime(2024, 1, 15, 10, 0, 0),
        finalizada=True
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    return prova_id, questao_id, sub.id


def test_get_all_avaliacoes_professor_owner(client_both):
    """Professor who owns the prova can see all avaliacoes."""
    with client_both.professor() as prof:
        prova_id, questao_id, sub_id = _create_prova_with_questao_and_submissao(prof, client_both.db)

        response = prof.get(f"/avaliacoes/prova/{prova_id}/todas")
        assert response.status_code == 200
        avaliacoes = response.json()
        assert len(avaliacoes) == 1
        assert avaliacoes[0]["questao_id"] == questao_id
        assert avaliacoes[0]["aluno_id"] == 1
        assert avaliacoes[0]["codigo_submetido"] == "print('hello world')"
        assert avaliacoes[0]["nota"] is None  # No grade yet
        assert "data_submissao" in avaliacoes[0]


def test_get_all_avaliacoes_prova_not_found(client_professor):
    """Prova that doesn't exist returns 404."""
    response = client_professor.get("/avaliacoes/prova/9999/todas")
    assert response.status_code == 404


def test_get_all_avaliacoes_not_owner(client_both):
    """Professor who does NOT own the prova gets 403."""
    from app.models.professor_model import Professor
    from app.models.prova_model import Prova
    from datetime import datetime

    other_prof = Professor(nome="Outro Prof", email="outro@ccc.ufcg.edu.br")
    client_both.db.add(other_prof)
    client_both.db.commit()
    client_both.db.refresh(other_prof)

    prova = Prova(
        titulo="Prova Alheia",
        descricao="De outro professor",
        data_aplicacao="2024-01-01T08:00:00",
        data_fim="2024-12-31T23:59:00",
        professor_id=other_prof.id,
        linguagem="python",
        emails_permitidos=[]
    )
    client_both.db.add(prova)
    client_both.db.commit()
    client_both.db.refresh(prova)

    with client_both.professor() as prof:
        response = prof.get(f"/avaliacoes/prova/{prova.id}/todas")
        assert response.status_code == 403


def test_get_my_avaliacoes_student(client_both):
    """Student can see their own avaliacoes for a prova."""
    with client_both.professor() as prof:
        prova_id, questao_id, sub_id = _create_prova_with_questao_and_submissao(prof, client_both.db)

    with client_both.aluno() as aluno:
        response = aluno.get(f"/avaliacoes/prova/{prova_id}/me")
        assert response.status_code == 200
        avaliacoes = response.json()
        assert len(avaliacoes) == 1
        assert avaliacoes[0]["aluno_id"] == 1
        assert avaliacoes[0]["questao_id"] == questao_id


def test_get_my_avaliacoes_prova_not_found(client_aluno):
    """Student requesting avaliacoes for non-existent prova gets 404."""
    response = client_aluno.get("/avaliacoes/prova/9999/me")
    assert response.status_code == 404


def test_update_nota_professor_owner(client_both):
    """Professor who owns the prova can update nota."""
    with client_both.professor() as prof:
        prova_id, questao_id, sub_id = _create_prova_with_questao_and_submissao(prof, client_both.db)

        response = prof.put(f"/avaliacoes/{sub_id}/nota", json={"nota": 8.5})
        assert response.status_code == 200
        assert response.json()["nota"] == 8.5

        avaliacoes = prof.get(f"/avaliacoes/prova/{prova_id}/todas").json()
        assert avaliacoes[0]["nota"] == 8.5


def test_update_nota_submissao_not_found(client_professor):
    """Updating nota for non-existent submissao returns 404."""
    response = client_professor.put("/avaliacoes/9999/nota", json={"nota": 7.0})
    assert response.status_code == 404


def test_update_nota_not_owner(client_both):
    """Professor who does NOT own the prova cannot update nota."""
    from app.models.professor_model import Professor
    from app.models.submissao_model import Submissao
    from app.models.prova_model import Prova
    from app.models.questao_model import Questao
    from datetime import datetime

    other_prof = Professor(nome="Outro Prof", email="outro@ccc.ufcg.edu.br")
    client_both.db.add(other_prof)
    client_both.db.commit()
    client_both.db.refresh(other_prof)

    prova = Prova(
        titulo="Prova Alheia",
        descricao="De outro prof",
        data_aplicacao="2024-01-01T08:00:00",
        data_fim="2024-12-31T23:59:00",
        professor_id=other_prof.id,
        linguagem="python",
        emails_permitidos=[]
    )
    client_both.db.add(prova)
    client_both.db.commit()
    client_both.db.refresh(prova)

    questao = Questao(
        prova_id=prova.id,
        titulo="Questao",
        descricao="Descricao",
        exemplo_input1="",
        exemplo_output1="output",
        peso=10.0
    )
    client_both.db.add(questao)
    client_both.db.commit()
    client_both.db.refresh(questao)

    sub = Submissao(
        aluno_id=1,
        prova_id=prova.id,
        questao_id=questao.id,
        codigo_submetido="code",
        data_envio=datetime(2024, 1, 15, 10, 0, 0),
        finalizada=True
    )
    client_both.db.add(sub)
    client_both.db.commit()
    client_both.db.refresh(sub)

    with client_both.professor() as prof:
        response = prof.put(f"/avaliacoes/{sub.id}/nota", json={"nota": 10.0})
        assert response.status_code == 403


def test_student_cannot_update_nota(client_both):
    """Students cannot access the nota update endpoint (professor-only)."""
    with client_both.professor() as prof:
        prova_id, questao_id, sub_id = _create_prova_with_questao_and_submissao(prof, client_both.db)

    with client_both.aluno() as aluno:
        response = aluno.put(f"/avaliacoes/{sub_id}/nota", json={"nota": 10.0})
        assert response.status_code == 403


def test_student_cannot_view_all_avaliacoes(client_both):
    """Students cannot access the /todas endpoint (professor-only)."""
    with client_both.professor() as prof:
        prova_id, _, _ = _create_prova_with_questao_and_submissao(prof, client_both.db)

    with client_both.aluno() as aluno:
        response = aluno.get(f"/avaliacoes/prova/{prova_id}/todas")
        assert response.status_code == 403


def test_nota_visible_to_student_after_grading(client_both):
    """After professor grades, student can see the nota via /me endpoint."""
    with client_both.professor() as prof:
        prova_id, questao_id, sub_id = _create_prova_with_questao_and_submissao(prof, client_both.db)

        prof.put(f"/avaliacoes/{sub_id}/nota", json={"nota": 9.0})

    with client_both.aluno() as aluno:
        response = aluno.get(f"/avaliacoes/prova/{prova_id}/me")
        assert response.status_code == 200
        avaliacoes = response.json()
        assert avaliacoes[0]["nota"] == 9.0
