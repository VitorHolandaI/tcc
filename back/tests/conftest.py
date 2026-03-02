import os
os.environ["TESTING"] = "true"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.core.auth_dependency import get_current_user, get_current_professor, get_current_aluno, CurrentUser

from app.models.professor_model import Professor
from app.models.aluno_model import Aluno
from app.models.prova_model import Prova
from app.models.questao_model import Questao
from app.models.prova_monitoramento_model import ProvaMonitoramento
from app.models.submissao_model import Submissao

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def mock_professor_user():
    """Returns a professor CurrentUser"""
    return CurrentUser(
        uid="test-prof-uid-123",
        email="professor.teste@ccc.ufcg.edu.br",
        name="Professor Teste"
    )


def mock_aluno_user():
    """Returns an aluno CurrentUser"""
    return CurrentUser(
        uid="test-aluno-uid-123",
        email="aluno.teste@gmail.com",  # Note: NOT @ccc, so is_aluno() returns True
        name="Aluno Teste"
    )


async def async_mock_professor():
    """Async version for get_current_professor override"""
    return CurrentUser(
        uid="test-prof-uid-123",
        email="professor.teste@ccc.ufcg.edu.br",
        name="Professor Teste"
    )


async def async_mock_aluno():
    """Async version for get_current_aluno override"""
    return CurrentUser(
        uid="test-aluno-uid-123",
        email="aluno.teste@gmail.com",
        name="Aluno Teste"
    )


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def override_get_db(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass
    return _override


@pytest.fixture
def client_professor(db_session):
    """Client authenticated as professor"""
    from app.models.professor_model import Professor

    professor = Professor(
        nome="Professor Teste",
        email="professor.teste@ccc.ufcg.edu.br"
    )
    db_session.add(professor)
    db_session.commit()

    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_user] = async_mock_professor
    app.dependency_overrides[get_current_professor] = async_mock_professor

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client_aluno(db_session):
    """Client authenticated as aluno"""
    from app.models.aluno_model import Aluno

    aluno = Aluno(
        nome="Aluno Teste",
        email="aluno.teste@gmail.com",
        matricula="999999"
    )
    db_session.add(aluno)
    db_session.commit()

    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_user] = async_mock_aluno
    app.dependency_overrides[get_current_aluno] = async_mock_aluno

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client_both(db_session):
    """
    Returns both professor and aluno clients sharing the same database.
    Useful for testing workflows that involve both users.

    Usage:
        - Use with context manager: `with client_both.professor() as prof:`
        - Access database directly: `client_both.db`
    """
    from app.models.professor_model import Professor
    from app.models.aluno_model import Aluno

    professor = Professor(
        nome="Professor Teste",
        email="professor.teste@ccc.ufcg.edu.br"
    )
    aluno = Aluno(
        nome="Aluno Teste",
        email="aluno.teste@gmail.com",
        matricula="999999"
    )
    db_session.add(professor)
    db_session.add(aluno)
    db_session.commit()

    app.dependency_overrides[get_db] = override_get_db(db_session)

    class Clients:
        def __init__(self):
            self.db = db_session

        def professor(self):
            """Returns a context manager for professor client"""
            app.dependency_overrides[get_current_user] = async_mock_professor
            app.dependency_overrides[get_current_professor] = async_mock_professor
            if get_current_aluno in app.dependency_overrides:
                del app.dependency_overrides[get_current_aluno]

            return TestClient(app)

        def aluno(self):
            """Returns a context manager for aluno client"""
            app.dependency_overrides[get_current_user] = async_mock_aluno
            app.dependency_overrides[get_current_aluno] = async_mock_aluno
            if get_current_professor in app.dependency_overrides:
                del app.dependency_overrides[get_current_professor]

            return TestClient(app)

    clients = Clients()
    yield clients

    app.dependency_overrides.clear()