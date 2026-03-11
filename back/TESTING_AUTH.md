# Testing with Authentication

## Overview

This backend uses Firebase Authentication in production, but mocks authentication during tests using FastAPI's dependency injection system.

## How It Works

### Production (Real Authentication)

In production, endpoints require real Firebase JWT tokens:

```python
@router.post("/", response_model=ProvaResponse, status_code=201)
def create_prova(
    prova: ProvaCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    # Only authenticated professors can create provas
    # Firebase token is validated by get_current_professor
```

### Testing (Mocked Authentication)

During tests, authentication is mocked in [tests/conftest.py](tests/conftest.py):

```python
# Mock functions return test users
def mock_get_current_professor():
    return CurrentUser(
        uid="test-prof-uid-123",
        email="professor.teste@ccc.ufcg.edu.br",
        name="Professor Teste"
    )

# Override dependencies for all tests
app.dependency_overrides[get_current_professor] = mock_get_current_professor
```

This allows tests to run without:
- Setting up Firebase Admin SDK
- Generating real JWT tokens
- Managing test Firebase accounts

## Test Setup

The [conftest.py](tests/conftest.py) file automatically:

1. **Mocks authentication dependencies** - No real tokens needed
2. **Creates default users** - Professor and Aluno with matching emails
3. **Cleans database before each test** - Fresh state for every test
4. **Provides test client** - Ready-to-use FastAPI TestClient

## Default Test Users

Created automatically before each test:

### Professor
- **Email:** `professor.teste@ccc.ufcg.edu.br`
- **Name:** Professor Teste
- **UID:** test-prof-uid-123

### Aluno
- **Email:** `aluno.teste@ccc.ufcg.edu.br`
- **Name:** Aluno Teste
- **UID:** test-aluno-uid-123
- **Matrícula:** 999999

## Running Tests

```bash
cd /home/vitor/git/tcc/back
source env/bin/activate
pytest -v
```

All 37 tests should pass:
```
============================== 37 passed in ~8s ==============================
```

## Important Notes

 **Production Security**
- Authentication mocks are ONLY active during tests
- Real Firebase authentication is required in production
- Never deploy with `app.dependency_overrides` set

 **Benefits**
- Tests run fast (no external Firebase calls)
- No Firebase test project needed
- Easy to maintain and debug
- Follows FastAPI best practices

## Adding New Protected Endpoints

When creating new authenticated endpoints:

1. Use the appropriate dependency:
   ```python
   current_user: CurrentUser = Depends(get_current_professor) # For professors
   current_user: CurrentUser = Depends(get_current_aluno) # For students
   ```

2. Tests will automatically use mocked authentication

3. No changes needed to existing test setup

## Troubleshooting

### Tests fail with 403 Forbidden
- Check if `app.dependency_overrides` is set in conftest.py
- Verify test is importing from the correct app instance

### Tests fail with "Professor não encontrado"
- Ensure conftest.py creates default professor/aluno
- Check email matches the mocked user email
- Verify database cleanup is working

### Production returns test data
- CRITICAL: Check if `app.dependency_overrides` is empty
- This should NEVER happen in production
- Overrides are only set during test execution
