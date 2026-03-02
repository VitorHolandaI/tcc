from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.auth_dependency import CurrentUser, get_current_user, get_current_professor
from app.core.ownership import verify_professor_owns_prova, verify_professor_owns_questao
from app.schemas.questao_schema import QuestaoCreate, QuestaoResponse
from app.repositories.questao_repository import QuestaoRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.aluno_repository import AlunoRepository
from app.models.aluno_model import Aluno
from app.models.professor_model import Professor

router = APIRouter(prefix="/questoes", tags=["Questoes"])


@router.post("/", response_model=QuestaoResponse, status_code=201)
def create_questao(
    questao: QuestaoCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """Create a new questao (only professor who owns the prova)"""
    verify_professor_owns_prova(questao.prova_id, current_user, db)

    repo = QuestaoRepository(db)
    return repo.create(questao)


@router.get("/{questao_id}", response_model=QuestaoResponse)
def get_questao(
    questao_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Get a questao by ID (with permission check)"""
    repo = QuestaoRepository(db)
    questao = repo.get_by_id(questao_id)
    if not questao:
        raise HTTPException(status_code=404, detail="Questão não encontrada")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(questao.prova_id)
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada")

    if current_user.is_professor():
        if prova.professor.email != current_user.email:
            raise HTTPException(status_code=403, detail="Você não tem permissão para ver esta questão")

    elif current_user.is_aluno():
        aluno_repo = AlunoRepository(db)
        aluno = aluno_repo.get_by_email(current_user.email)
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")

        if prova.emails_permitidos and aluno.email not in prova.emails_permitidos:
            raise HTTPException(status_code=403, detail="Você não tem permissão para ver esta questão")

    return questao


@router.get("/prova/{prova_id}", response_model=List[QuestaoResponse])
def list_questoes_by_prova(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all questions for a prova.
    - Professors can see questions if they own the prova.
    - Students can see questions only if they are on the whitelist AND within the test time window.
    """
    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(status_code=404, detail="Prova não encontrada.")

    if current_user.is_professor():
        if prova.professor.email != current_user.email:
            raise HTTPException(
                status_code=403, detail="Você não tem permissão para ver as questões desta prova.")

    elif current_user.is_aluno():
        aluno_repo = AlunoRepository(db)
        aluno = aluno_repo.get_by_email(current_user.email)
        if not aluno:
            raise HTTPException(
                status_code=404, detail="Aluno não encontrado no sistema.")

        if prova.emails_permitidos and aluno.email not in prova.emails_permitidos:
            raise HTTPException(
                status_code=403, detail="Você não tem permissão para realizar esta prova.")

        try:
            from zoneinfo import ZoneInfo
            SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

            now = datetime.now(SAO_PAULO_TZ)
            data_inicio = datetime.fromisoformat(prova.data_aplicacao).astimezone(SAO_PAULO_TZ)
            data_fim = datetime.fromisoformat(prova.data_fim).astimezone(SAO_PAULO_TZ)

            if not (data_inicio <= now <= data_fim):
                raise HTTPException(
                    status_code=403, detail="A prova não está disponível neste momento.")
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=500, detail="Formato de data inválido na configuração da prova.")

    else:
        raise HTTPException(
            status_code=403, detail="Tipo de usuário inválido.")

    repo = QuestaoRepository(db)
    return repo.list_by_prova(prova_id)


@router.put("/{questao_id}", response_model=QuestaoResponse)
def update_questao(
    questao_id: int,
    questao_data: QuestaoCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """Update a questao (only professor who owns the prova)"""
    verify_professor_owns_questao(questao_id, current_user, db)

    repo = QuestaoRepository(db)
    updated_questao = repo.update(questao_id, questao_data)
    if not updated_questao:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    return updated_questao


@router.delete("/{questao_id}", status_code=204)
def delete_questao(
    questao_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """Delete a questao (only professor who owns the prova)"""
    verify_professor_owns_questao(questao_id, current_user, db)

    repo = QuestaoRepository(db)
    questao = repo.delete(questao_id)
    if not questao:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    return None
