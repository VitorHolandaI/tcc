from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.firebase_config import verify_firebase_token
from typing import Optional

security = HTTPBearer()

def _get_db():
    from app.core.database import get_db
    return get_db

class CurrentUser:
    """Class to hold current authenticated user information"""
    def __init__(self, uid: str, email: str, name: Optional[str] = None):
        self.uid = uid
        self.email = email
        self.name = name

    def is_professor(self) -> bool:
        """Check if user is a professor based on email domain"""
        if not self.email:
            return False
        PROFESSOR_WHITELIST = {"vitor.holanda@ccc.ufcg.edu.br"}
        return (self.email.endswith("@computacao.ufcg.edu.br") or
                self.email.endswith("@ccc.ufcg.edu.br") or
                self.email in PROFESSOR_WHITELIST)

    def is_aluno(self) -> bool:
        """Check if user is an aluno (student)"""
        return not self.is_professor()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependency to get current authenticated user from Firebase token

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: CurrentUser = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    try:
        token = credentials.credentials
        decoded_token = verify_firebase_token(token)

        return CurrentUser(
            uid=decoded_token.get("uid"),
            email=decoded_token.get("email"),
            name=decoded_token.get("name")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_professor(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(_get_db())
) -> CurrentUser:
    """
    Dependency to ensure current user is a professor and exists in database

    Usage:
        @router.get("/professor-only")
        async def professor_route(
            professor: CurrentUser = Depends(get_current_professor)
        ):
            return {"professor": professor.email}
    """
    if not current_user.is_professor():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only professors can access this resource"
        )

    from app.repositories.professor_repository import ProfessorRepository
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Professor não encontrado no banco de dados. Por favor, faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user

async def get_current_aluno(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(_get_db())
) -> CurrentUser:
    """
    Dependency to ensure current user is an aluno (student) and exists in database

    Usage:
        @router.get("/aluno-only")
        async def aluno_route(aluno: CurrentUser = Depends(get_current_aluno)):
            return {"aluno": aluno.email}
    """
    if not current_user.is_aluno():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this resource"
        )

    from app.repositories.aluno_repository import AlunoRepository
    aluno_repo = AlunoRepository(db)
    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Aluno não encontrado no banco de dados. Por favor, faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[CurrentUser]:
    """
    Optional authentication - returns None if no token provided

    Usage:
        @router.get("/maybe-protected")
        async def maybe_protected(user: Optional[CurrentUser] = Depends(get_current_user_optional)):
            if user:
                return {"authenticated": True, "user": user.email}
            return {"authenticated": False}
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        decoded_token = verify_firebase_token(token)

        return CurrentUser(
            uid=decoded_token.get("uid"),
            email=decoded_token.get("email"),
            name=decoded_token.get("name")
        )
    except:
        return None
