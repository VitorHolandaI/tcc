from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth_dependency import CurrentUser, get_current_professor
from app.core.ownership import get_current_professor_id
from app.schemas.professor_schema import ProfessorCreate, ProfessorResponse
from app.repositories.professor_repository import ProfessorRepository

router = APIRouter(prefix="/professores", tags=["Professores"])


@router.post("/", response_model=ProfessorResponse, status_code=201)
def create_professor(professor: ProfessorCreate, db: Session = Depends(get_db)):
    """
    Get or create professor (called after Firebase login).

    This endpoint is public because it's called by the frontend after
    Firebase authentication to ensure the user exists in the database.
    """
    repo = ProfessorRepository(db)

    existing_professor = repo.get_by_email(professor.email)
    if existing_professor:
        return existing_professor

    return repo.create(professor)


@router.get("/me", response_model=ProfessorResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """Get current professor's profile"""
    repo = ProfessorRepository(db)
    professor = repo.get_by_email(current_user.email)
    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    return professor


@router.put("/me", response_model=ProfessorResponse)
def update_my_profile(
    professor_data: ProfessorCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """Update current professor's profile"""
    professor_id = get_current_professor_id(current_user, db)
    repo = ProfessorRepository(db)
    updated = repo.update(professor_id, professor_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Professor não encontrado")
    return updated
