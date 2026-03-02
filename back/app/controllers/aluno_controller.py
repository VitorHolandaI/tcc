from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth_dependency import CurrentUser, get_current_aluno, get_current_user
from app.core.ownership import get_current_aluno_id
from app.schemas.aluno_schema import AlunoCreate, AlunoResponse
from app.repositories.aluno_repository import AlunoRepository

router = APIRouter(prefix="/alunos", tags=["Alunos"])


@router.post("/", response_model=AlunoResponse, status_code=201)
def create_aluno(aluno: AlunoCreate, db: Session = Depends(get_db)):
    """
    Get or create aluno (called after Firebase login).

    This endpoint is public because it's called by the frontend after
    Firebase authentication to ensure the user exists in the database.
    """
    repo = AlunoRepository(db)

    existing_aluno = repo.get_by_email(aluno.email)
    if existing_aluno:
        return existing_aluno

    return repo.create(aluno)


@router.get("/me", response_model=AlunoResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """Get current student's profile"""
    repo = AlunoRepository(db)
    aluno = repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return aluno


@router.put("/me", response_model=AlunoResponse)
def update_my_profile(
    aluno_data: AlunoCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """Update current student's profile"""
    aluno_id = get_current_aluno_id(current_user, db)
    repo = AlunoRepository(db)
    updated = repo.update(aluno_id, aluno_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return updated


@router.get("/{aluno_id}", response_model=AlunoResponse)
def get_aluno_by_id(
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get aluno by ID (any authenticated user can access)"""
    repo = AlunoRepository(db)
    aluno = repo.get_by_id(aluno_id)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")
    return aluno
