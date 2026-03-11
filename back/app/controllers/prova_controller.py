from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.ownership import verify_professor_owns_prova, verify_aluno_can_access_prova, get_current_professor_id
from app.schemas.prova_schema import ProvaCreate, ProvaResponse, ProvaComResultadosResponse
from app.repositories.prova_repository import ProvaRepository
from app.repositories.professor_repository import ProfessorRepository
from app.repositories.aluno_repository import AlunoRepository
from app.core.auth_dependency import get_current_user, get_current_professor, get_current_aluno, CurrentUser
from app.models.submissao_model import Submissao

def _submissao_to_avaliacao(sub: Submissao) -> dict:
    """Convert a Submissao model to the Avaliacao response format the frontend expects."""
    return {
        "id": sub.id,
        "questao_id": sub.questao_id,
        "aluno_id": sub.aluno_id,
        "codigo_submetido": sub.codigo_submetido,
        "resultado_execucao": sub.resultado_execucao,
        "nota": sub.nota,
        "data_submissao": sub.data_envio.isoformat() if sub.data_envio else None,
        "finalizada": sub.finalizada,
    }

router = APIRouter(prefix="/provas", tags=["Provas"])

@router.post("/", response_model=ProvaResponse, status_code=201)
def create_prova(
    prova: ProvaCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """Create a new prova (only professors)"""
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado no banco de dados")

    prova.professor_id = professor.id

    repo = ProvaRepository(db)
    return repo.create(prova)

@router.get("/{prova_id}", response_model=ProvaResponse)
def get_prova(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get a specific prova.

    - Professors can access their own provas
    - Students can only access provas they are enrolled in (emails_permitidos) and during valid time
    """
    repo = ProvaRepository(db)
    prova = repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")

    if current_user.is_professor():
        professor_id = get_current_professor_id(current_user, db)
        if prova.professor_id != professor_id:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para acessar esta prova"
            )

    elif current_user.is_aluno():
        verify_aluno_can_access_prova(prova_id, current_user, db, mode="ver")

    return prova

@router.get("/{prova_id}/meu-resultado", response_model=ProvaComResultadosResponse)
def get_my_prova_with_results(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    Retorna os detalhes de uma prova junto com as avaliações do aluno logado.
    """
    aluno_repo = AlunoRepository(db)
    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")

    verify_aluno_can_access_prova(prova_id, current_user, db, mode="ver")

    submissoes = db.query(Submissao).filter(
        Submissao.prova_id == prova_id,
        Submissao.aluno_id == aluno.id
    ).all()

    avaliacoes = [_submissao_to_avaliacao(s) for s in submissoes]

    response_data = {
        **prova.__dict__,
        "avaliacoes": avaliacoes
    }
    
    return response_data

@router.put("/{prova_id}", response_model=ProvaResponse)
def update_prova(
    prova_id: int,
    prova_data: ProvaCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """Update a prova (only the professor who created it)"""
    verify_professor_owns_prova(prova_id, current_user, db)

    repo = ProvaRepository(db)
    updated_prova = repo.update(prova_id, prova_data)
    if not updated_prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    return updated_prova

@router.delete("/{prova_id}", status_code=204)
def delete_prova(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """Delete a prova (only the professor who created it)"""
    verify_professor_owns_prova(prova_id, current_user, db)

    repo = ProvaRepository(db)
    prova = repo.delete(prova_id)
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")
    return None

@router.get("/me/agendadas", response_model=List[ProvaResponse])
def list_my_provas_agendadas(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """List scheduled provas (before data_aplicacao)"""
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")

    repo = ProvaRepository(db)
    all_provas = repo.list_by_professor(professor.id)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    scheduled_provas = [p for p in all_provas if p.data_aplicacao > now]

    return scheduled_provas

@router.get("/me/em-andamento", response_model=List[ProvaResponse])
def list_my_provas_em_andamento(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """List provas currently in progress (between data_aplicacao and data_fim)"""
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")

    repo = ProvaRepository(db)
    all_provas = repo.list_by_professor(professor.id)

    now = datetime.now(timezone.utc)

    def _parse(date_str):
        dt = datetime.fromisoformat(date_str)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    in_progress_provas = [p for p in all_provas if _parse(p.data_aplicacao) <= now <= _parse(p.data_fim)]

    return in_progress_provas

@router.get("/me/passadas", response_model=List[ProvaResponse])
def list_my_provas_passadas(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """List past provas (after data_fim)"""
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")

    repo = ProvaRepository(db)
    all_provas = repo.list_by_professor(professor.id)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    past_provas = [p for p in all_provas if p.data_fim < now]

    return past_provas

@router.get("/me/todas", response_model=List[ProvaResponse])
def list_my_all_provas(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """List all provas created by the authenticated professor"""
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(status_code=404, detail="Professor não encontrado")

    repo = ProvaRepository(db)
    return repo.list_by_professor(professor.id)

@router.get("/aluno/disponiveis", response_model=List[ProvaResponse])
def list_aluno_provas_disponiveis(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    List all provas available for the authenticated aluno.

    A prova is available if:
    - emails_permitidos is empty (available to all), OR
    - aluno's email is in emails_permitidos list
    """
    aluno_repo = AlunoRepository(db)
    aluno = aluno_repo.get_by_email(current_user.email)

    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado")

    repo = ProvaRepository(db)
    all_provas = repo.list_all()

    available_provas = []
    for prova in all_provas:
        if not prova.emails_permitidos or len(prova.emails_permitidos) == 0:
            available_provas.append(prova)
        elif aluno.email in prova.emails_permitidos:
            available_provas.append(prova)

    return available_provas
