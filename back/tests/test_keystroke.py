"""
Tests for Keystroke Dynamics feature.

Tests cover:
- Saving keystroke data to a submission
- Concatenation of keystroke data on subsequent saves
- Ownership validation
- Data format compatibility with Roberto's analyzer
- Professor access to keystroke data via submission endpoint
"""
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.prova_model import Prova
from app.models.questao_model import Questao
from app.models.submissao_model import Submissao

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


def _create_prova_with_questao(db_session, professor_email="professor.teste@ccc.ufcg.edu.br"):
    """Helper: create a prova with a question in valid time window"""
    from app.models.professor_model import Professor
    professor = db_session.query(Professor).filter_by(email=professor_email).first()

    now = datetime.now(SAO_PAULO_TZ)
    prova = Prova(
        titulo="Prova Keystroke",
        descricao="Teste de keystroke dynamics",
        data_aplicacao=(now - timedelta(hours=1)).isoformat(),
        data_fim=(now + timedelta(hours=1)).isoformat(),
        professor_id=professor.id,
        linguagem="python",
        emails_permitidos=["aluno.teste@gmail.com"],
        max_saidas=3
    )
    db_session.add(prova)
    db_session.commit()
    db_session.refresh(prova)

    questao = Questao(
        prova_id=prova.id,
        titulo="Questão 1",
        descricao="Escreva hello world",
        exemplo_input1="",
        exemplo_output1="hello world",
        peso=1.0
    )
    db_session.add(questao)
    db_session.commit()
    db_session.refresh(questao)

    return prova, questao


def _create_submissao(db_session, aluno_email="aluno.teste@gmail.com"):
    """Helper: create a prova, questao, and submissao"""
    from app.models.aluno_model import Aluno

    prova, questao = _create_prova_with_questao(db_session)
    aluno = db_session.query(Aluno).filter_by(email=aluno_email).first()

    submissao = Submissao(
        aluno_id=aluno.id,
        prova_id=prova.id,
        questao_id=questao.id,
        codigo_submetido="print('hello world')",
        data_envio=datetime.now(SAO_PAULO_TZ),
        finalizada=False
    )
    db_session.add(submissao)
    db_session.commit()
    db_session.refresh(submissao)

    return submissao


def _sample_keystroke_events(n=5):
    """Generate sample keystroke events in Roberto's format"""
    events = []
    base_time = datetime.now(SAO_PAULO_TZ)
    for i in range(n):
        events.append({
            "key": chr(97 + (i % 26)),  # a, b, c, ...
            "timestamp": (base_time + timedelta(milliseconds=i * 200)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "application": "Browser",
            "flight_time": round(0.2 + (i * 0.01), 3) if i > 0 else None,
            "hold_time": round(0.1 + (i * 0.005), 3),
            "command_type": None
        })
    return events


class TestKeystrokeSave:
    """Tests for PUT /submissoes/keystroke/{submissao_id}"""

    def test_save_keystroke_data_first_time(self, client_both):
        """First save creates keystroke_dynamics field"""
        db = client_both.db
        submissao = _create_submissao(db)
        events = _sample_keystroke_events(5)

        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao.id}",
                json=events
            )

        assert response.status_code == 200
        data = response.json()
        assert data["total_events"] == 5
        assert data["submissao_id"] == submissao.id

        db.refresh(submissao)
        assert submissao.keystroke_dynamics is not None
        assert len(submissao.keystroke_dynamics) == 5

    def test_save_keystroke_data_concatenation(self, client_both):
        """Subsequent saves concatenate with existing data"""
        db = client_both.db
        submissao = _create_submissao(db)

        first_events = _sample_keystroke_events(3)
        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao.id}",
                json=first_events
            )
        assert response.status_code == 200
        assert response.json()["total_events"] == 3

        second_events = _sample_keystroke_events(5)
        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao.id}",
                json=second_events
            )
        assert response.status_code == 200
        assert response.json()["total_events"] == 8  # 3 + 5

        third_events = _sample_keystroke_events(2)
        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao.id}",
                json=third_events
            )
        assert response.status_code == 200
        assert response.json()["total_events"] == 10  # 3 + 5 + 2

    def test_save_keystroke_submissao_not_found(self, client_aluno):
        """Returns 404 for non-existent submissao"""
        events = _sample_keystroke_events(3)
        response = client_aluno.put(
            "/submissoes/keystroke/99999",
            json=events
        )
        assert response.status_code == 404

    def test_save_keystroke_wrong_student(self, client_both):
        """Student cannot save keystroke data to another student's submission"""
        db = client_both.db

        from app.models.aluno_model import Aluno
        other_aluno = Aluno(
            nome="Outro Aluno",
            email="outro.aluno@gmail.com",
            matricula="888888"
        )
        db.add(other_aluno)
        db.commit()

        prova, questao = _create_prova_with_questao(db)
        submissao = Submissao(
            aluno_id=other_aluno.id,
            prova_id=prova.id,
            questao_id=questao.id,
            codigo_submetido="print('test')",
            data_envio=datetime.now(SAO_PAULO_TZ),
            finalizada=False
        )
        db.add(submissao)
        db.commit()
        db.refresh(submissao)

        events = _sample_keystroke_events(3)
        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao.id}",
                json=events
            )
        assert response.status_code == 403

    def test_save_empty_keystroke_data(self, client_both):
        """Saving empty array should work"""
        db = client_both.db
        submissao = _create_submissao(db)

        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao.id}",
                json=[]
            )
        assert response.status_code == 200
        assert response.json()["total_events"] == 0


class TestKeystrokeDataFormat:
    """Tests for keystroke data format compatibility with Roberto's analyzer"""

    def test_data_format_matches_analyzer_requirements(self, client_both):
        """Verify saved data has all fields needed by Roberto's analyzer"""
        db = client_both.db
        submissao = _create_submissao(db)

        events = [
            {
                "key": "a",
                "timestamp": "2024-01-01 12:00:00.000",
                "application": "Browser",
                "flight_time": None,
                "hold_time": 0.123,
                "command_type": None
            },
            {
                "key": "b",
                "timestamp": "2024-01-01 12:00:00.200",
                "application": "Browser",
                "flight_time": 0.200,
                "hold_time": 0.098,
                "command_type": None
            },
            {
                "key": "ctrl+v",
                "timestamp": "2024-01-01 12:00:00.500",
                "application": "Browser",
                "flight_time": 0.300,
                "hold_time": 0.050,
                "command_type": "paste"
            }
        ]

        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao.id}",
                json=events
            )
        assert response.status_code == 200

        db.refresh(submissao)
        stored = submissao.keystroke_dynamics
        assert len(stored) == 3

        evt = stored[0]
        assert "key" in evt
        assert "timestamp" in evt
        assert "application" in evt
        assert "flight_time" in evt
        assert "hold_time" in evt
        assert "command_type" in evt

        paste_evt = stored[2]
        assert paste_evt["command_type"] == "paste"
        assert paste_evt["key"] == "ctrl+v"

    def test_all_command_types_saved(self, client_both):
        """All command types recognized by analyzer are saved correctly"""
        db = client_both.db
        submissao = _create_submissao(db)

        events = [
            {"key": "ctrl+v", "timestamp": "2024-01-01 12:00:00.000", "application": "Browser",
             "flight_time": None, "hold_time": 0.1, "command_type": "paste"},
            {"key": "ctrl+c", "timestamp": "2024-01-01 12:00:00.100", "application": "Browser",
             "flight_time": 0.1, "hold_time": 0.1, "command_type": "copy"},
            {"key": "ctrl+x", "timestamp": "2024-01-01 12:00:00.200", "application": "Browser",
             "flight_time": 0.1, "hold_time": 0.1, "command_type": "cut"},
            {"key": "Backspace", "timestamp": "2024-01-01 12:00:00.300", "application": "Browser",
             "flight_time": 0.1, "hold_time": 0.1, "command_type": "backspace"},
            {"key": "ArrowLeft", "timestamp": "2024-01-01 12:00:00.400", "application": "Browser",
             "flight_time": 0.1, "hold_time": 0.1, "command_type": "cursor_movement"},
        ]

        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao.id}",
                json=events
            )
        assert response.status_code == 200

        db.refresh(submissao)
        stored = submissao.keystroke_dynamics
        command_types = [e["command_type"] for e in stored]
        assert "paste" in command_types
        assert "copy" in command_types
        assert "cut" in command_types
        assert "backspace" in command_types
        assert "cursor_movement" in command_types


class TestKeystrokeProfessorAccess:
    """Tests for professor accessing keystroke data via submissions"""

    def test_professor_can_see_submissions_with_keystroke_data(self, client_both):
        """Professor can view all submissions including keystroke_dynamics"""
        db = client_both.db

        submissao = _create_submissao(db)
        submissao.keystroke_dynamics = _sample_keystroke_events(10)
        db.commit()
        db.refresh(submissao)

        with client_both.professor() as client:
            response = client.get(
                f"/submissoes/prova-professor/{submissao.prova_id}"
            )

        assert response.status_code == 200
        submissions = response.json()
        assert len(submissions) >= 1

    def test_professor_cannot_access_other_prova_submissions(self, client_both):
        """Professor cannot see submissions for provas they don't own"""
        db = client_both.db
        from app.models.professor_model import Professor

        other_prof = Professor(
            nome="Outro Professor",
            email="outro.prof@ccc.ufcg.edu.br"
        )
        db.add(other_prof)
        db.commit()

        now = datetime.now(SAO_PAULO_TZ)
        other_prova = Prova(
            titulo="Prova do Outro",
            descricao="Prova de outro professor",
            data_aplicacao=(now - timedelta(hours=1)).isoformat(),
            data_fim=(now + timedelta(hours=1)).isoformat(),
            professor_id=other_prof.id,
            linguagem="python",
            emails_permitidos=[],
            max_saidas=3
        )
        db.add(other_prova)
        db.commit()

        with client_both.professor() as client:
            response = client.get(
                f"/submissoes/prova-professor/{other_prova.id}"
            )

        assert response.status_code == 403


class TestKeystrokeSubmissaoIntegration:
    """Tests for keystroke dynamics integration with submission workflow"""

    def test_submit_code_then_save_keystroke(self, client_both):
        """Full workflow: submit code, then save keystroke data"""
        db = client_both.db
        prova, questao = _create_prova_with_questao(db)

        with client_both.aluno() as client:
            response = client.post("/submissoes/", json={
                "prova_id": prova.id,
                "questao_id": questao.id,
                "codigo_submetido": "print('hello world')"
            })
        assert response.status_code == 201
        submissao_id = response.json()["id"]

        events = _sample_keystroke_events(10)
        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao_id}",
                json=events
            )
        assert response.status_code == 200
        assert response.json()["total_events"] == 10

    def test_auto_save_simulation(self, client_both):
        """Simulates auto-save behavior: multiple saves over time"""
        db = client_both.db
        submissao = _create_submissao(db)

        total_events = 0
        for batch in range(5):
            events = _sample_keystroke_events(20)  # 20 events per batch
            with client_both.aluno() as client:
                response = client.put(
                    f"/submissoes/keystroke/{submissao.id}",
                    json=events
                )
            assert response.status_code == 200
            total_events += 20
            assert response.json()["total_events"] == total_events

        db.refresh(submissao)
        assert len(submissao.keystroke_dynamics) == 100  # 5 * 20

    def test_keystroke_data_persists_after_code_update(self, client_both):
        """Keystroke data should persist even after code is updated"""
        db = client_both.db
        prova, questao = _create_prova_with_questao(db)

        with client_both.aluno() as client:
            response = client.post("/submissoes/", json={
                "prova_id": prova.id,
                "questao_id": questao.id,
                "codigo_submetido": "print('v1')"
            })
        assert response.status_code == 201
        submissao_id = response.json()["id"]

        events = _sample_keystroke_events(10)
        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao_id}",
                json=events
            )
        assert response.status_code == 200

        with client_both.aluno() as client:
            response = client.post("/submissoes/", json={
                "prova_id": prova.id,
                "questao_id": questao.id,
                "codigo_submetido": "print('v2')"
            })
        assert response.status_code == 201

        submissao = db.query(Submissao).filter_by(id=submissao_id).first()
        db.refresh(submissao)
        assert submissao.keystroke_dynamics is not None
        assert len(submissao.keystroke_dynamics) == 10
        assert submissao.codigo_submetido == "print('v2')"

    def test_large_keystroke_dataset(self, client_both):
        """Test with a large number of keystroke events (simulating long exam)"""
        db = client_both.db
        submissao = _create_submissao(db)

        events = _sample_keystroke_events(500)
        with client_both.aluno() as client:
            response = client.put(
                f"/submissoes/keystroke/{submissao.id}",
                json=events
            )
        assert response.status_code == 200
        assert response.json()["total_events"] == 500
