# Automated Tests

## Overview

The automated tests use **pytest** + **FastAPI TestClient**. No real server is started — requests go directly into the ASGI app in-process, making tests fast and fully isolated.

```
Test → TestClient(app) → FastAPI routes → SQLite (in-memory)
                                        ↑
                           dependency_overrides swap out:
                           - PostgreSQL → SQLite
                           - Firebase auth → fake user
```

## Running Tests

```bash
# All backend test suites
./run-all-tests.sh --back

# Main API only (116 tests)
cd back && .venv/bin/python -m pytest tests/ -v

# Keystroke service only (11 tests)
cd back/keystroke-service && ../.venv/bin/python -m pytest test_main.py -v

# Similarity service only (39 tests)
cd back/similarity-service && ../.venv/bin/python -m pytest -v
```

The venv is at `back/.venv` (Python 3.11). Create it with:
```bash
cd back
uv venv .venv --python 3.11
uv pip install -r requirements.txt -r keystroke-service/requirements.txt -r similarity-service/requirements.txt --upgrade
```

---

## How TestClient Works

`TestClient` (from `fastapi.testclient`) wraps the app with `httpx` and calls it as an ASGI app directly — no TCP socket, no port, no uvicorn. This means:

- Tests run offline (no Firebase, no PostgreSQL needed)
- No port conflicts
- Requests complete synchronously, even for `async` routes

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.get("/provas/1")   # goes directly into FastAPI, no HTTP
```

---

## Dependency Overrides

FastAPI's dependency injection system (`Depends`) is replaced at test time using `app.dependency_overrides`. This is a dict that maps the real dependency function to a replacement.

### Swapping the Database

The real app uses PostgreSQL via `get_db`. Tests replace it with a fresh SQLite file:

```python
# conftest.py
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db(db_session):
    def _override():
        yield db_session
    return _override

app.dependency_overrides[get_db] = override_get_db(db_session)
```

### Bypassing Firebase Auth

The real `get_current_user` validates a Firebase JWT token. Tests replace it with a function that returns a hardcoded fake user:

```python
async def async_mock_professor():
    return CurrentUser(
        uid="test-prof-uid-123",
        email="professor.teste@ccc.ufcg.edu.br",
        name="Professor Teste"
    )

app.dependency_overrides[get_current_user] = async_mock_professor
app.dependency_overrides[get_current_professor] = async_mock_professor
```

All three auth dependencies are overridden to ensure every layer of the auth chain uses the fake user:

| Dependency | Role |
|---|---|
| `get_current_user` | Returns any authenticated user |
| `get_current_professor` | Returns user + verifies professor role |
| `get_current_aluno` | Returns user + verifies student role |

Overrides are cleared after each test with `app.dependency_overrides.clear()`.

---

## Test Fixtures

Fixtures are defined in `back/tests/conftest.py` and provide pre-configured clients with test data already seeded.

### `db_session` — Fresh database per test

```python
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)   # create all tables
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)     # wipe all tables after test
```

`scope="function"` means this runs for every individual test — each test starts with a completely empty database.

### `client_professor` — Authenticated professor client

Creates a professor row in the test DB and returns a client that is already authenticated as that professor:

```python
@pytest.fixture
def client_professor(db_session):
    professor = Professor(nome="Professor Teste", email="professor.teste@ccc.ufcg.edu.br")
    db_session.add(professor)
    db_session.commit()

    app.dependency_overrides[get_db] = override_get_db(db_session)
    app.dependency_overrides[get_current_user] = async_mock_professor
    app.dependency_overrides[get_current_professor] = async_mock_professor

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
```

### `client_aluno` — Authenticated student client

Same pattern but seeds an `Aluno` row and uses the student mock:

```python
@pytest.fixture
def client_aluno(db_session):
    aluno = Aluno(nome="Aluno Teste", email="aluno.teste@gmail.com", matricula="999999")
    db_session.add(aluno)
    db_session.commit()

    app.dependency_overrides[get_current_user] = async_mock_aluno
    app.dependency_overrides[get_current_aluno] = async_mock_aluno
    ...
```

### `client_both` — Shared DB with both users

Used for tests that need both a professor and a student to interact (e.g. testing ownership checks, whitelist access):

```python
@pytest.fixture
def client_both(db_session):
    # Seeds both professor and aluno into the same DB
    # Returns an object with .professor() and .aluno() context managers

with client_both.professor() as prof_client:
    response = prof_client.get(f"/provas/{prova_id}")

with client_both.aluno() as aluno_client:
    response = aluno_client.get(f"/provas/{prova_id}")
```

---

## Role Detection

`is_professor()` checks the email domain:

```python
def is_professor(self) -> bool:
    return (self.email.endswith("@computacao.ufcg.edu.br") or
            self.email.endswith("@ccc.ufcg.edu.br") or
            self.email in PROFESSOR_WHITELIST)
```

The test mock professor uses `professor.teste@ccc.ufcg.edu.br` (matches `@ccc.ufcg.edu.br`).
The test mock student uses `aluno.teste@gmail.com` (no match → `is_aluno()` returns True).

---

## Keystroke Service Tests

The keystroke service (`back/keystroke-service/`) is a separate FastAPI app. Its tests follow the same pattern with one extra layer: `MainSessionLocal` (the connection to the main app's database) is mocked with `unittest.mock.patch`.

`back/keystroke-service/conftest.py` adds `back/` to `sys.path` so the service can import `from app.core.database import Base`:

```python
# conftest.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

Cross-DB calls are patched per test:

```python
@patch("main.MainSessionLocal")
def test_start_analysis_no_submissao(mock_main_db_class, client_professor):
    mock_main_db = MagicMock()
    mock_main_db.query.return_value.filter.return_value.first.return_value = None
    mock_main_db_class.return_value = mock_main_db

    response = client_professor.post("/analyze/1/1")
    assert response.status_code == 404
```

---

## Test Suite Summary

| Suite | Location | Tests | What it covers |
|---|---|---|---|
| Main API | `back/tests/` | 116 | provas, questoes, submissoes, alunos, professores, auth, recording, monitoring |
| Keystroke Service | `back/keystroke-service/` | 11 | analysis endpoints, auth, DB state transitions |
| Similarity Service | `back/similarity-service/` | 39 | analyzer logic, API endpoints |

Total: **166 tests**.
