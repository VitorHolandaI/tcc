from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.auth_dependency import CurrentUser, get_current_professor, get_current_aluno
from app.repositories.submissao_repository import SubmissaoRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.professor_repository import ProfessorRepository
from app.repositories.aluno_repository import AlunoRepository
from app.models.submissao_model import Submissao
from app.schemas.avaliacao_schema import AvaliacaoResponse, NotaUpdate

router = APIRouter(prefix="/avaliacoes", tags=["Avaliações"])


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


def _verify_professor_owns_prova(db: Session, email: str, prova_id: int):
    """Verify that the professor owns the prova. Returns (professor, prova) or raises HTTPException."""
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(email)
    if not professor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prova não encontrada")

    if prova.professor_id != professor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar as avaliações desta prova"
        )
    return professor, prova


@router.get("/prova/{prova_id}/todas", response_model=List[AvaliacaoResponse])
def get_all_avaliacoes_for_prova(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Retorna todas as avaliações (submissões) de uma prova.
    Apenas o professor dono da prova pode acessar.
    """
    _verify_professor_owns_prova(db, current_user.email, prova_id)

    submissoes = db.query(Submissao).filter(Submissao.prova_id == prova_id).all()
    return [_submissao_to_avaliacao(s) for s in submissoes]


@router.get("/prova/{prova_id}/me", response_model=List[AvaliacaoResponse])
def get_my_avaliacoes_for_prova(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    Retorna as avaliações (submissões) do aluno autenticado para uma prova.
    """
    aluno_repo = AlunoRepository(db)
    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prova não encontrada")

    submissoes = db.query(Submissao).filter(
        Submissao.prova_id == prova_id,
        Submissao.aluno_id == aluno.id
    ).all()
    return [_submissao_to_avaliacao(s) for s in submissoes]


@router.put("/{submissao_id}/nota", response_model=AvaliacaoResponse)
def update_nota(
    submissao_id: int,
    nota_data: NotaUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Atualiza a nota de uma submissão.
    Apenas o professor dono da prova pode atribuir notas.
    """
    submissao_repo = SubmissaoRepository(db)
    submissao = submissao_repo.get_by_id(submissao_id)
    if not submissao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submissão não encontrada")

    _verify_professor_owns_prova(db, current_user.email, submissao.prova_id)

    submissao.nota = nota_data.nota
    db.commit()
    db.refresh(submissao)

    return _submissao_to_avaliacao(submissao)
