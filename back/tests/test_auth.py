"""
Tests for authentication and authorization logic.

Tests cover:
- CurrentUser class behavior (is_professor, is_aluno)
- Role-based access control
- Cross-role access prevention
"""
import pytest
from app.core.auth_dependency import CurrentUser


class TestCurrentUser:
    """Tests for the CurrentUser class"""

    def test_professor_email_ccc(self):
        """CCC email should be identified as professor"""
        user = CurrentUser(uid="123", email="fulano@ccc.ufcg.edu.br", name="Prof")
        assert user.is_professor() is True
        assert user.is_aluno() is False

    def test_professor_email_computacao(self):
        """Computacao email should be identified as professor"""
        user = CurrentUser(uid="123", email="fulano@computacao.ufcg.edu.br", name="Prof")
        assert user.is_professor() is True
        assert user.is_aluno() is False

    def test_aluno_gmail(self):
        """Gmail email should be identified as student"""
        user = CurrentUser(uid="123", email="aluno@gmail.com", name="Aluno")
        assert user.is_professor() is False
        assert user.is_aluno() is True

    def test_aluno_other_domain(self):
        """Non-ufcg email should be identified as student"""
        user = CurrentUser(uid="123", email="user@outlook.com", name="User")
        assert user.is_professor() is False
        assert user.is_aluno() is True

    def test_empty_email(self):
        """Empty email should not be professor"""
        user = CurrentUser(uid="123", email="", name="User")
        assert user.is_professor() is False

    def test_none_email(self):
        """None email should not be professor"""
        user = CurrentUser(uid="123", email=None, name="User")
        assert user.is_professor() is False

    def test_user_properties(self):
        """User properties should be accessible"""
        user = CurrentUser(uid="abc-123", email="test@gmail.com", name="Test User")
        assert user.uid == "abc-123"
        assert user.email == "test@gmail.com"
        assert user.name == "Test User"


class TestRoleBasedAccess:
    """Tests for role-based access control on endpoints"""

    def test_professor_cannot_access_aluno_endpoints(self, client_professor):
        """Professor should get 403 on aluno-only endpoints"""
        # /submissoes/me/todas requires get_current_aluno
        response = client_professor.get("/submissoes/me/todas")
        assert response.status_code == 403

    def test_aluno_cannot_create_prova(self, client_aluno):
        """Aluno should get 403 on professor-only endpoints"""
        response = client_aluno.post("/provas/", json={
            "titulo": "Prova Ilegal",
            "descricao": "Tentativa",
            "data_aplicacao": "2026-01-01T10:00:00",
            "data_fim": "2026-01-01T12:00:00",
            "professor_id": 1,
            "linguagem": "python",
            "emails_permitidos": [],
            "max_saidas": 3
        })
        assert response.status_code == 403

    def test_aluno_cannot_delete_prova(self, client_aluno):
        """Aluno should get 403 trying to delete a prova"""
        response = client_aluno.delete("/provas/1")
        assert response.status_code == 403

    def test_aluno_cannot_create_questao(self, client_aluno):
        """Aluno should get 403 trying to create a questao"""
        response = client_aluno.post("/questoes/", json={
            "prova_id": 1,
            "titulo": "Illegal Question",
            "descricao": "Tentativa",
            "exemplo_input1": "1",
            "exemplo_output1": "1",
            "peso": 1.0
        })
        assert response.status_code == 403


class TestCrossOwnershipAccess:
    """Tests for cross-ownership prevention"""

    def test_professor_cannot_access_other_provas(self, client_both):
        """Professor A should not see Professor B's provas"""
        from app.models.professor_model import Professor
        from app.models.prova_model import Prova
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        db = client_both.db
        SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

        other_prof = Professor(nome="Outro", email="outro@ccc.ufcg.edu.br")
        db.add(other_prof)
        db.commit()

        now = datetime.now(SAO_PAULO_TZ)
        other_prova = Prova(
            titulo="Prova Secreta",
            descricao="Nao deveria ser visivel",
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
            response = client.get(f"/provas/{other_prova.id}")
        assert response.status_code == 403

    def test_professor_cannot_update_other_prova(self, client_both):
        """Professor A cannot update Professor B's prova"""
        from app.models.professor_model import Professor
        from app.models.prova_model import Prova
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        db = client_both.db
        SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

        other_prof = Professor(nome="Outro", email="outro@ccc.ufcg.edu.br")
        db.add(other_prof)
        db.commit()

        now = datetime.now(SAO_PAULO_TZ)
        other_prova = Prova(
            titulo="Prova Alheia",
            descricao="Tentativa de update",
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
            response = client.put(f"/provas/{other_prova.id}", json={
                "titulo": "Hackeado!",
                "descricao": "Nao deveria funcionar",
                "data_aplicacao": (now - timedelta(hours=1)).isoformat(),
                "data_fim": (now + timedelta(hours=1)).isoformat(),
                "professor_id": other_prof.id,
                "linguagem": "python",
                "emails_permitidos": [],
                "max_saidas": 3
            })
        assert response.status_code in [403, 404]

    def test_professor_cannot_delete_other_prova(self, client_both):
        """Professor A cannot delete Professor B's prova"""
        from app.models.professor_model import Professor
        from app.models.prova_model import Prova
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        db = client_both.db
        SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

        other_prof = Professor(nome="Outro", email="outro@ccc.ufcg.edu.br")
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
            response = client.delete(f"/provas/{other_prova.id}")
        assert response.status_code in [403, 404]

    def test_student_not_in_whitelist_cannot_access_prova(self, client_both):
        """Student not in whitelist cannot access prova"""
        from app.models.prova_model import Prova
        from app.models.professor_model import Professor
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        db = client_both.db
        SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

        professor = db.query(Professor).first()
        now = datetime.now(SAO_PAULO_TZ)

        prova = Prova(
            titulo="Prova Restrita",
            descricao="",
            data_aplicacao=(now - timedelta(hours=1)).isoformat(),
            data_fim=(now + timedelta(hours=1)).isoformat(),
            professor_id=professor.id,
            linguagem="python",
            emails_permitidos=["outro.aluno@gmail.com"],  # Different student
            max_saidas=3
        )
        db.add(prova)
        db.commit()

        with client_both.aluno() as client:
            response = client.get(f"/provas/{prova.id}")
        assert response.status_code == 403

    def test_student_in_whitelist_can_access_prova(self, client_both):
        """Student in whitelist can access prova"""
        from app.models.prova_model import Prova
        from app.models.professor_model import Professor
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        db = client_both.db
        SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

        professor = db.query(Professor).first()
        now = datetime.now(SAO_PAULO_TZ)

        prova = Prova(
            titulo="Prova Permitida",
            descricao="",
            data_aplicacao=(now - timedelta(hours=1)).isoformat(),
            data_fim=(now + timedelta(hours=1)).isoformat(),
            professor_id=professor.id,
            linguagem="python",
            emails_permitidos=["aluno.teste@gmail.com"],  # Our test student
            max_saidas=3
        )
        db.add(prova)
        db.commit()

        with client_both.aluno() as client:
            response = client.get(f"/provas/{prova.id}")
        assert response.status_code == 200

    def test_student_can_access_open_prova(self, client_both):
        """Student can access prova with empty whitelist (open to all)"""
        from app.models.prova_model import Prova
        from app.models.professor_model import Professor
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        db = client_both.db
        SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

        professor = db.query(Professor).first()
        now = datetime.now(SAO_PAULO_TZ)

        prova = Prova(
            titulo="Prova Aberta",
            descricao="",
            data_aplicacao=(now - timedelta(hours=1)).isoformat(),
            data_fim=(now + timedelta(hours=1)).isoformat(),
            professor_id=professor.id,
            linguagem="python",
            emails_permitidos=[],  # Open to all
            max_saidas=3
        )
        db.add(prova)
        db.commit()

        with client_both.aluno() as client:
            response = client.get(f"/provas/{prova.id}")
        assert response.status_code == 200
