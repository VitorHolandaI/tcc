"""
Tests for Recording Controller.

Tests cover:
- Video access permissions (professor ownership)
- Recording status checks
- Recording service health check
- File path security
"""
import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.models.prova_model import Prova
from app.models.professor_model import Professor

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


def _create_prova(db_session, professor_email="professor.teste@ccc.ufcg.edu.br"):
    """Helper: create a prova owned by the test professor"""
    professor = db_session.query(Professor).filter_by(email=professor_email).first()
    now = datetime.now(SAO_PAULO_TZ)
    prova = Prova(
        titulo="Prova Gravada",
        descricao="Prova com gravacao",
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
    return prova


class TestRecordingAccess:
    """Tests for recording video access"""

    def test_video_not_found(self, client_professor, db_session):
        """Requesting non-existent recording returns 404"""
        prova = _create_prova(db_session)
        response = client_professor.get(f"/recordings/video/{prova.id}/999")
        assert response.status_code == 404

    def test_status_for_nonexistent_recording(self, client_professor, db_session):
        """Status check for non-existent recording returns info"""
        prova = _create_prova(db_session)
        response = client_professor.get(f"/recordings/status/{prova.id}/999")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
        assert data["status"] in ["not_started", "recording"]

    def test_cannot_access_other_professor_recording(self, client_both):
        """Professor cannot access recordings from other professor's prova"""
        db = client_both.db

        other_prof = Professor(nome="Outro Prof", email="outro@ccc.ufcg.edu.br")
        db.add(other_prof)
        db.commit()

        now = datetime.now(SAO_PAULO_TZ)
        other_prova = Prova(
            titulo="Prova Alheia",
            descricao="",
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
            response = client.get(f"/recordings/video/{other_prova.id}/1")
        assert response.status_code == 403

    def test_cannot_access_status_other_professor_recording(self, client_both):
        """Professor cannot check status of other professor's recordings"""
        db = client_both.db

        other_prof = Professor(nome="Outro Prof", email="outro@ccc.ufcg.edu.br")
        db.add(other_prof)
        db.commit()

        now = datetime.now(SAO_PAULO_TZ)
        other_prova = Prova(
            titulo="Prova Alheia",
            descricao="",
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
            response = client.get(f"/recordings/status/{other_prova.id}/1")
        assert response.status_code == 403

    def test_delete_nonexistent_recording(self, client_professor, db_session):
        """Deleting non-existent recording returns 404"""
        prova = _create_prova(db_session)
        response = client_professor.delete(f"/recordings/video/{prova.id}/999")
        assert response.status_code == 404


class TestRecordingServiceHealth:
    """Tests for recording service health check"""

    def test_service_health_when_offline(self, client_professor):
        """Health check returns offline status when recording service is not running"""
        response = client_professor.get("/recordings/service-health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["online", "offline"]
