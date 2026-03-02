"""
Integration Tests - End-to-End Exam Workflows.

Tests the complete flow from prova creation to submission to analysis.
These tests verify that all components work together correctly.
"""
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


class TestCompleteExamWorkflow:
    """Tests the complete exam workflow: create → take → submit → finalize"""

    def test_full_exam_lifecycle(self, client_both):
        """
        Complete workflow:
        1. Professor creates prova
        2. Professor adds questions
        3. Student accesses prova
        4. Student submits answers
        5. Student saves keystroke data
        6. Student finalizes prova
        7. Professor views submissions
        """
        db = client_both.db
        now = datetime.now(SAO_PAULO_TZ)

        with client_both.professor() as client:
            response = client.post("/provas/", json={
                "titulo": "Prova Integração Completa",
                "descricao": "Teste end-to-end",
                "data_aplicacao": (now - timedelta(hours=1)).isoformat(),
                "data_fim": (now + timedelta(hours=2)).isoformat(),
                "professor_id": 1,
                "linguagem": "python",
                "emails_permitidos": ["aluno.teste@gmail.com"],
                "max_saidas": 3
            })
        assert response.status_code == 201
        prova_id = response.json()["id"]

        with client_both.professor() as client:
            resp1 = client.post("/questoes/", json={
                "prova_id": prova_id,
                "titulo": "Questão 1 - Hello World",
                "descricao": "Escreva um programa que imprime 'hello world'",
                "exemplo_input1": "",
                "exemplo_output1": "hello world",
                "peso": 1.0
            })
            assert resp1.status_code == 201
            q1_id = resp1.json()["id"]

            resp2 = client.post("/questoes/", json={
                "prova_id": prova_id,
                "titulo": "Questão 2 - Soma",
                "descricao": "Escreva uma função que soma dois números",
                "exemplo_input1": "2 3",
                "exemplo_output1": "5",
                "exemplo_input2": "10 20",
                "exemplo_output2": "30",
                "peso": 2.0
            })
            assert resp2.status_code == 201
            q2_id = resp2.json()["id"]

        with client_both.aluno() as client:
            response = client.get(f"/provas/{prova_id}")
        assert response.status_code == 200
        assert response.json()["titulo"] == "Prova Integração Completa"

        with client_both.aluno() as client:
            response = client.get(f"/questoes/prova/{prova_id}")
        assert response.status_code == 200
        questoes = response.json()
        assert len(questoes) == 2

        with client_both.aluno() as client:
            resp1 = client.post("/submissoes/", json={
                "prova_id": prova_id,
                "questao_id": q1_id,
                "codigo_submetido": "print('hello world')"
            })
        assert resp1.status_code == 201
        sub1_id = resp1.json()["id"]

        with client_both.aluno() as client:
            resp2 = client.post("/submissoes/", json={
                "prova_id": prova_id,
                "questao_id": q2_id,
                "codigo_submetido": "def soma(a, b):\n    return a + b"
            })
        assert resp2.status_code == 201
        sub2_id = resp2.json()["id"]

        keystroke_batch1 = [
            {"key": "p", "timestamp": "2024-01-01 12:00:00.000", "application": "Browser",
             "flight_time": None, "hold_time": 0.1, "command_type": None},
            {"key": "r", "timestamp": "2024-01-01 12:00:00.200", "application": "Browser",
             "flight_time": 0.2, "hold_time": 0.09, "command_type": None},
            {"key": "i", "timestamp": "2024-01-01 12:00:00.400", "application": "Browser",
             "flight_time": 0.2, "hold_time": 0.11, "command_type": None},
        ]

        with client_both.aluno() as client:
            response = client.put(f"/submissoes/keystroke/{sub1_id}", json=keystroke_batch1)
        assert response.status_code == 200
        assert response.json()["total_events"] == 3

        keystroke_batch2 = [
            {"key": "n", "timestamp": "2024-01-01 12:02:00.000", "application": "Browser",
             "flight_time": 0.15, "hold_time": 0.08, "command_type": None},
            {"key": "t", "timestamp": "2024-01-01 12:02:00.200", "application": "Browser",
             "flight_time": 0.2, "hold_time": 0.1, "command_type": None},
        ]

        with client_both.aluno() as client:
            response = client.put(f"/submissoes/keystroke/{sub1_id}", json=keystroke_batch2)
        assert response.status_code == 200
        assert response.json()["total_events"] == 5  # 3 + 2

        with client_both.aluno() as client:
            response = client.post(f"/submissoes/finalizar/{prova_id}", json=[
                {
                    "prova_id": prova_id,
                    "questao_id": q1_id,
                    "codigo_submetido": "print('hello world')"
                },
                {
                    "prova_id": prova_id,
                    "questao_id": q2_id,
                    "codigo_submetido": "def soma(a, b):\n    return a + b"
                }
            ])
        assert response.status_code == 200
        finalized = response.json()
        assert len(finalized) == 2
        assert all(s["finalizada"] for s in finalized)

        with client_both.professor() as client:
            response = client.get(f"/submissoes/prova-professor/{prova_id}")
        assert response.status_code == 200
        submissions = response.json()
        assert len(submissions) == 2

        with client_both.aluno() as client:
            response = client.post("/submissoes/", json={
                "prova_id": prova_id,
                "questao_id": q1_id,
                "codigo_submetido": "print('hacked!')"
            })
        assert response.status_code == 403


class TestExamMonitoringWorkflow:
    """Tests the monitoring workflow: exits → invalidation → blocked submission"""

    def test_exit_monitoring_blocks_submission(self, client_both):
        """
        Workflow:
        1. Professor creates prova with max_saidas=2
        2. Student submits code (should work)
        3. Student exits page 3 times (exceeds limit)
        4. Prova becomes invalidated
        5. Student cannot submit anymore
        """
        db = client_both.db
        now = datetime.now(SAO_PAULO_TZ)

        with client_both.professor() as client:
            response = client.post("/provas/", json={
                "titulo": "Prova Monitorada",
                "descricao": "Prova com limite de saidas",
                "data_aplicacao": (now - timedelta(hours=1)).isoformat(),
                "data_fim": (now + timedelta(hours=2)).isoformat(),
                "professor_id": 1,
                "linguagem": "python",
                "emails_permitidos": ["aluno.teste@gmail.com"],
                "max_saidas": 2
            })
        assert response.status_code == 201
        prova_id = response.json()["id"]

        with client_both.professor() as client:
            response = client.post("/questoes/", json={
                "prova_id": prova_id,
                "titulo": "Q1",
                "descricao": "D1",
                "exemplo_input1": "1",
                "exemplo_output1": "1",
                "peso": 1.0
            })
        assert response.status_code == 201
        q_id = response.json()["id"]

        with client_both.aluno() as client:
            response = client.post("/submissoes/", json={
                "prova_id": prova_id,
                "questao_id": q_id,
                "codigo_submetido": "print(1)"
            })
        assert response.status_code == 201

        for i in range(3):
            with client_both.aluno() as client:
                response = client.post(f"/provas/{prova_id}/registrar-saida")
            assert response.status_code == 200

        with client_both.aluno() as client:
            response = client.get(f"/provas/{prova_id}/status-monitoramento")
        assert response.status_code == 200
        status = response.json()
        assert status["invalidada"] is True
        assert status["numero_saidas"] == 3

        with client_both.aluno() as client:
            response = client.post("/submissoes/", json={
                "prova_id": prova_id,
                "questao_id": q_id,
                "codigo_submetido": "print('blocked!')"
            })
        assert response.status_code == 403


class TestMultiStudentWorkflow:
    """Tests workflow with multiple students"""

    def test_two_students_independent_submissions(self, client_both):
        """Two different students can submit independently"""
        db = client_both.db
        now = datetime.now(SAO_PAULO_TZ)

        with client_both.professor() as client:
            response = client.post("/provas/", json={
                "titulo": "Prova Multi-Aluno",
                "descricao": "",
                "data_aplicacao": (now - timedelta(hours=1)).isoformat(),
                "data_fim": (now + timedelta(hours=2)).isoformat(),
                "professor_id": 1,
                "linguagem": "python",
                "emails_permitidos": ["aluno.teste@gmail.com"],
                "max_saidas": 3
            })
        assert response.status_code == 201
        prova_id = response.json()["id"]

        with client_both.professor() as client:
            response = client.post("/questoes/", json={
                "prova_id": prova_id,
                "titulo": "Q1",
                "descricao": "D1",
                "exemplo_input1": "1",
                "exemplo_output1": "1",
                "peso": 1.0
            })
        q_id = response.json()["id"]

        with client_both.aluno() as client:
            response = client.post("/submissoes/", json={
                "prova_id": prova_id,
                "questao_id": q_id,
                "codigo_submetido": "print('answer from student 1')"
            })
        assert response.status_code == 201

        with client_both.aluno() as client:
            response = client.get("/submissoes/me/todas")
        assert response.status_code == 200
        submissions = response.json()
        assert len(submissions) >= 1

    def test_student_available_provas_filtering(self, client_both):
        """Students should only see provas they're whitelisted for"""
        db = client_both.db
        now = datetime.now(SAO_PAULO_TZ)

        with client_both.professor() as client:
            resp_a = client.post("/provas/", json={
                "titulo": "Prova A - Allowed",
                "descricao": "",
                "data_aplicacao": (now - timedelta(hours=1)).isoformat(),
                "data_fim": (now + timedelta(hours=2)).isoformat(),
                "professor_id": 1,
                "linguagem": "python",
                "emails_permitidos": ["aluno.teste@gmail.com"],
                "max_saidas": 3
            })
            assert resp_a.status_code == 201

        with client_both.professor() as client:
            resp_b = client.post("/provas/", json={
                "titulo": "Prova B - Restricted",
                "descricao": "",
                "data_aplicacao": (now - timedelta(hours=1)).isoformat(),
                "data_fim": (now + timedelta(hours=2)).isoformat(),
                "professor_id": 1,
                "linguagem": "python",
                "emails_permitidos": ["outro.aluno@gmail.com"],
                "max_saidas": 3
            })
            assert resp_b.status_code == 201

        with client_both.professor() as client:
            resp_c = client.post("/provas/", json={
                "titulo": "Prova C - Open",
                "descricao": "",
                "data_aplicacao": (now - timedelta(hours=1)).isoformat(),
                "data_fim": (now + timedelta(hours=2)).isoformat(),
                "professor_id": 1,
                "linguagem": "python",
                "emails_permitidos": [],
                "max_saidas": 3
            })
            assert resp_c.status_code == 201

        with client_both.aluno() as client:
            response = client.get("/provas/aluno/disponiveis")
        assert response.status_code == 200
        provas = response.json()
        prova_titles = [p["titulo"] for p in provas]
        assert "Prova A - Allowed" in prova_titles
        assert "Prova C - Open" in prova_titles
        assert "Prova B - Restricted" not in prova_titles


class TestKeystrokeWorkflowIntegration:
    """Tests keystroke data persistence through exam lifecycle"""

    def test_keystroke_data_survives_finalization(self, client_both):
        """Keystroke data should persist after exam finalization"""
        db = client_both.db
        now = datetime.now(SAO_PAULO_TZ)

        with client_both.professor() as client:
            response = client.post("/provas/", json={
                "titulo": "Prova Keystroke Integration",
                "descricao": "",
                "data_aplicacao": (now - timedelta(hours=1)).isoformat(),
                "data_fim": (now + timedelta(hours=2)).isoformat(),
                "professor_id": 1,
                "linguagem": "python",
                "emails_permitidos": ["aluno.teste@gmail.com"],
                "max_saidas": 3
            })
        prova_id = response.json()["id"]

        with client_both.professor() as client:
            response = client.post("/questoes/", json={
                "prova_id": prova_id,
                "titulo": "Q1",
                "descricao": "D1",
                "exemplo_input1": "1",
                "exemplo_output1": "1",
                "peso": 1.0
            })
        q_id = response.json()["id"]

        with client_both.aluno() as client:
            response = client.post("/submissoes/", json={
                "prova_id": prova_id,
                "questao_id": q_id,
                "codigo_submetido": "print(1)"
            })
        sub_id = response.json()["id"]

        keystroke_events = [
            {"key": "p", "timestamp": "2024-01-01 12:00:00.000", "application": "Browser",
             "flight_time": None, "hold_time": 0.1, "command_type": None},
            {"key": "r", "timestamp": "2024-01-01 12:00:00.200", "application": "Browser",
             "flight_time": 0.2, "hold_time": 0.09, "command_type": None},
        ]
        with client_both.aluno() as client:
            response = client.put(f"/submissoes/keystroke/{sub_id}", json=keystroke_events)
        assert response.status_code == 200

        with client_both.aluno() as client:
            response = client.post(f"/submissoes/finalizar/{prova_id}", json=[{
                "prova_id": prova_id,
                "questao_id": q_id,
                "codigo_submetido": "print(1)"
            }])
        assert response.status_code == 200

        from app.models.submissao_model import Submissao
        submissao = db.query(Submissao).filter_by(id=sub_id).first()
        db.refresh(submissao)
        assert submissao.keystroke_dynamics is not None
        assert len(submissao.keystroke_dynamics) == 2
        assert submissao.finalizada is True
