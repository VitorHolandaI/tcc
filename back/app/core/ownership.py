"""
Ownership verification utilities for authentication and authorization.

This module provides helper functions to verify that users have permission
to access or modify resources based on Firebase JWT token authentication.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.auth_dependency import CurrentUser


def verify_professor_owns_prova(
    prova_id: int,
    current_user: CurrentUser,
    db: Session
) -> None:
    """
    Verify that the current authenticated professor owns the prova.

    Args:
        prova_id: ID of the prova to check
        current_user: Current authenticated user (from JWT token)
        db: Database session

    Raises:
        HTTPException 404: If professor or prova not found
        HTTPException 403: If professor doesn't own the prova
    """
    from app.repositories.professor_repository import ProfessorRepository
    from app.repositories.prova_repository import ProvaRepository

    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)
    if not professor:
        raise HTTPException(
            status_code=404,
            detail="Professor não encontrado no banco de dados"
        )

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(
            status_code=404,
            detail="Prova não encontrada"
        )

    if prova.professor_id != professor.id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para modificar esta prova"
        )


def get_current_aluno_id(
    current_user: CurrentUser,
    db: Session
) -> int:
    """
    Get the database ID of the current authenticated student.

    Args:
        current_user: Current authenticated user (from JWT token)
        db: Database session

    Returns:
        The aluno's database ID

    Raises:
        HTTPException 404: If aluno not found in database
    """
    from app.repositories.aluno_repository import AlunoRepository

    aluno_repo = AlunoRepository(db)
    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(
            status_code=404,
            detail="Aluno não encontrado no banco de dados"
        )
    return aluno.id


def get_current_professor_id(
    current_user: CurrentUser,
    db: Session
) -> int:
    """
    Get the database ID of the current authenticated professor.

    Args:
        current_user: Current authenticated user (from JWT token)
        db: Database session

    Returns:
        The professor's database ID

    Raises:
        HTTPException 404: If professor not found in database
    """
    from app.repositories.professor_repository import ProfessorRepository

    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)
    if not professor:
        raise HTTPException(
            status_code=404,
            detail="Professor não encontrado no banco de dados"
        )
    return professor.id


def verify_professor_owns_questao(
    questao_id: int,
    current_user: CurrentUser,
    db: Session
) -> None:
    """
    Verify that the current professor owns the prova that contains this questao.

    Args:
        questao_id: ID of the questao to check
        current_user: Current authenticated user (from JWT token)
        db: Database session

    Raises:
        HTTPException 404: If professor, questao, or prova not found
        HTTPException 403: If professor doesn't own the prova
    """
    from app.repositories.questao_repository import QuestaoRepository
    from app.repositories.professor_repository import ProfessorRepository

    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)
    if not professor:
        raise HTTPException(
            status_code=404,
            detail="Professor não encontrado no banco de dados"
        )

    questao_repo = QuestaoRepository(db)
    questao = questao_repo.get_by_id(questao_id)
    if not questao:
        raise HTTPException(
            status_code=404,
            detail="Questão não encontrada"
        )

    if not questao.prova:
        raise HTTPException(
            status_code=500,
            detail="Questão não está associada a uma prova"
        )

    if questao.prova.professor_id != professor.id:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para modificar esta questão"
        )


def verify_aluno_can_access_prova(
    prova_id: int,
    current_user: CurrentUser,
    db: Session,
    mode: str = "fazer"
) -> None:
    """
    Verify that the current student can access this prova.

    Modes:
    - "fazer": aluno wants to start/continue prova. Requires em andamento.
    - "ver": aluno wants to view result. Requires passada + aluno participated.

    Raises:
        HTTPException 404: If prova not found
        HTTPException 403: If student cannot access the prova
    """
    from app.repositories.prova_repository import ProvaRepository
    from app.repositories.aluno_repository import AlunoRepository
    from app.repositories.questao_repository import QuestaoRepository

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(
            status_code=404,
            detail="Prova não encontrada"
        )

    emails_permitidos = prova.emails_permitidos or []
    if emails_permitidos and current_user.email not in emails_permitidos:
        raise HTTPException(
            status_code=403,
            detail="Você não está autorizado a acessar esta prova"
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    if mode == "fazer":
        if now > prova.data_fim:
            raise HTTPException(
                status_code=403,
                detail="Esta prova já foi encerrada"
            )
        if now < prova.data_aplicacao:
            raise HTTPException(
                status_code=403,
                detail="Esta prova ainda não começou"
            )

    elif mode == "ver":
        if now < prova.data_aplicacao:
            raise HTTPException(
                status_code=403,
                detail="Esta prova ainda não começou"
            )

        aluno_repo = AlunoRepository(db)
        aluno = aluno_repo.get_by_email(current_user.email)
        if not aluno:
            raise HTTPException(status_code=404, detail="Aluno não encontrado")

        questao_repo = QuestaoRepository(db)
        questoes = questao_repo.list_by_prova(prova_id)
