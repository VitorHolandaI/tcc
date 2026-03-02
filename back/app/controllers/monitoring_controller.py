from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth_dependency import CurrentUser, get_current_aluno
from app.schemas.prova_monitoramento_schema import ProvaMonitoramentoResponse
from app.repositories.prova_monitoramento_repository import ProvaMonitoramentoRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.aluno_repository import AlunoRepository

router = APIRouter(prefix="/provas", tags=["Monitoramento de Provas"])


@router.post("/{prova_id}/registrar-saida")
def registrar_saida_prova(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    Registra que o aluno saiu da página da prova.
    Incrementa o contador de saídas e invalida a prova se exceder o limite.

    Retorna o status atual de monitoramento.
    """
    aluno_repo = AlunoRepository(db)
    prova_repo = ProvaRepository(db)
    monit_repo = ProvaMonitoramentoRepository(db)

    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado no sistema."
        )

    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prova não encontrada."
        )

    if prova.emails_permitidos and aluno.email not in prova.emails_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para realizar esta prova."
        )

    monitoramento = monit_repo.create_or_update(aluno.id, prova.id)

    # max_saidas=0 significa sem limite (monitoramento desabilitado)
    if prova.max_saidas > 0 and monitoramento.numero_saidas > prova.max_saidas and not monitoramento.invalidada:
        monitoramento = monit_repo.invalidar_prova(aluno.id, prova.id)

    return {
        "numero_saidas": monitoramento.numero_saidas,
        "max_saidas": prova.max_saidas,
        "invalidada": monitoramento.invalidada,
        "saidas_restantes": max(0, prova.max_saidas - monitoramento.numero_saidas)
    }


@router.get("/{prova_id}/status-monitoramento")
def get_status_monitoramento(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    Retorna o status atual de monitoramento da prova para o aluno.
    Usado ao carregar a prova para verificar se já foi invalidada.
    """
    aluno_repo = AlunoRepository(db)
    prova_repo = ProvaRepository(db)
    monit_repo = ProvaMonitoramentoRepository(db)

    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado no sistema."
        )

    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prova não encontrada."
        )

    if prova.emails_permitidos and aluno.email not in prova.emails_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para realizar esta prova."
        )

    monitoramento = monit_repo.get_by_aluno_and_prova(aluno.id, prova.id)

    if not monitoramento:
        return {
            "numero_saidas": 0,
            "max_saidas": prova.max_saidas,
            "invalidada": False,
            "saidas_restantes": prova.max_saidas
        }

    return {
        "numero_saidas": monitoramento.numero_saidas,
        "max_saidas": prova.max_saidas,
        "invalidada": monitoramento.invalidada,
        "saidas_restantes": max(0, prova.max_saidas - monitoramento.numero_saidas)
    }
