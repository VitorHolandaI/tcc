from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List

from app.core.database import get_db
from app.core.auth_dependency import CurrentUser, get_current_aluno, get_current_professor
from app.schemas.submissao_schema import SubmissaoCreate, SubmissaoResponse
from app.repositories.submissao_repository import SubmissaoRepository
from app.repositories.aluno_repository import AlunoRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.questao_repository import QuestaoRepository
from app.repositories.professor_repository import ProfessorRepository
from app.models.submissao_model import Submissao

router = APIRouter(prefix="/submissoes", tags=["Submissões"])

@router.get("/me/todas", response_model=List[SubmissaoResponse])
def get_all_my_submissions(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    Obtém todas as submissões de um aluno.
    """
    aluno_repo = AlunoRepository(db)
    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")

    submissao_repo = SubmissaoRepository(db)
    return submissao_repo.get_all_by_aluno_id(aluno_id=aluno.id)

@router.get("/{questao_id}", response_model=Optional[SubmissaoResponse])
def get_submissao_for_questao(
    questao_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    Obtém a submissão de um aluno para uma questão específica.
    """
    aluno_repo = AlunoRepository(db)
    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado.")

    submissao_repo = SubmissaoRepository(db)
    submissao = submissao_repo.get_by_aluno_and_questao(aluno_id=aluno.id, questao_id=questao_id)
    
    return submissao

@router.post("/", response_model=SubmissaoResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_submissao(
    submissao_data: SubmissaoCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    Cria ou atualiza uma submissão para uma questão de uma prova.
    Este endpoint executa as seguintes validações:
    1. Se o aluno logado existe no banco de dados.
    2. Se a prova e a questão existem.
    3. Se a questão pertence à prova.
    4. Se o email do aluno está na lista de emails permitidos da prova.
    5. Se a submissão está dentro da janela de tempo (data de aplicação e fim) da prova.
    """
    aluno_repo = AlunoRepository(db)
    prova_repo = ProvaRepository(db)
    questao_repo = QuestaoRepository(db)
    submissao_repo = SubmissaoRepository(db)

    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado no sistema.")

    prova = prova_repo.get_by_id(submissao_data.prova_id)
    if not prova:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prova não encontrada.")

    questao = questao_repo.get_by_id(submissao_data.questao_id)
    if not questao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questão não encontrada.")

    if questao.prova_id != prova.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A questão não pertence à prova especificada.")

    if prova.emails_permitidos and aluno.email not in prova.emails_permitidos:
        raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Você não tem permissão para realizar esta prova."
    )

    try:
        from zoneinfo import ZoneInfo
        SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

        now = datetime.now(SAO_PAULO_TZ)
        data_inicio = datetime.fromisoformat(prova.data_aplicacao).astimezone(SAO_PAULO_TZ)
        data_fim = datetime.fromisoformat(prova.data_fim).astimezone(SAO_PAULO_TZ)

        if not (data_inicio <= now <= data_fim):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A prova não está disponível neste momento.")
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Formato de data inválido na configuração da prova.")

    from app.repositories.prova_monitoramento_repository import ProvaMonitoramentoRepository
    monit_repo = ProvaMonitoramentoRepository(db)

    if monit_repo.is_prova_invalidada(aluno_id=aluno.id, prova_id=prova.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta prova foi invalidada por excesso de saídas da página."
        )

    if submissao_repo.are_submissions_finalized(aluno_id=aluno.id, prova_id=prova.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta prova já foi finalizada e não pode mais ser editada."
        )

    submissao = submissao_repo.create_or_update(submissao_data, aluno_id=aluno.id)

    return submissao

@router.post("/finalizar/{prova_id}", response_model=List[SubmissaoResponse])
def finalizar_prova(
    prova_id: int,
    submissoes_data: List[SubmissaoCreate],
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    Finaliza a prova, salvando todas as submissões e marcando-as como finalizadas.
    Após finalizar, o aluno não poderá mais editar suas respostas.
    """
    aluno_repo = AlunoRepository(db)
    prova_repo = ProvaRepository(db)
    questao_repo = QuestaoRepository(db)
    submissao_repo = SubmissaoRepository(db)

    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado no sistema.")

    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prova não encontrada.")

    if prova.emails_permitidos and aluno.email not in prova.emails_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para realizar esta prova."
        )

    try:
        from zoneinfo import ZoneInfo
        from datetime import timedelta
        SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")

        now = datetime.now(SAO_PAULO_TZ)
        data_inicio = datetime.fromisoformat(prova.data_aplicacao).astimezone(SAO_PAULO_TZ)
        data_fim = datetime.fromisoformat(prova.data_fim).astimezone(SAO_PAULO_TZ)

        tolerancia_minutos = 5
        data_fim_com_tolerancia = data_fim + timedelta(minutes=tolerancia_minutos)

        if now > data_fim_com_tolerancia:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"O prazo para finalizar esta prova expirou em {data_fim.strftime('%d/%m/%Y às %H:%M')}."
            )

        if now < data_inicio:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Esta prova ainda não começou."
            )
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Formato de data inválido na configuração da prova."
        )

    from app.repositories.prova_monitoramento_repository import ProvaMonitoramentoRepository
    monit_repo = ProvaMonitoramentoRepository(db)

    if monit_repo.is_prova_invalidada(aluno_id=aluno.id, prova_id=prova.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta prova foi invalidada por excesso de saídas da página e não pode ser finalizada."
        )

    if submissao_repo.are_submissions_finalized(aluno_id=aluno.id, prova_id=prova.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta prova já foi finalizada anteriormente."
        )

    submissoes_salvas = []
    for submissao_data in submissoes_data:
        if submissao_data.prova_id != prova_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Submissão para questão {submissao_data.questao_id} não pertence à prova {prova_id}."
            )

        questao = questao_repo.get_by_id(submissao_data.questao_id)
        if not questao or questao.prova_id != prova_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Questão {submissao_data.questao_id} não encontrada ou não pertence à prova."
            )

        submissao = submissao_repo.create_or_update(
            submissao_data,
            aluno_id=aluno.id,
            finalizada=True
        )
        submissoes_salvas.append(submissao)

    return submissoes_salvas


@router.get("/prova-professor/{prova_id}", response_model=List[SubmissaoResponse])
def get_all_submissions_for_prova(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Retorna TODAS as submissões de uma prova (para o professor ver detalhes).

    SEGURANÇA: Apenas professor dono da prova pode acessar.
    """
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professor não encontrado"
        )

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)

    if not prova:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prova não encontrada"
        )

    if prova.professor_id != professor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar essas submissões"
        )

    submissoes = db.query(Submissao).filter(Submissao.prova_id == prova_id).all()

    return submissoes


@router.put("/keystroke/{submissao_id}")
def update_keystroke_dynamics(
    submissao_id: int,
    keystroke_data: List[dict],
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_aluno)
):
    """
    Atualiza os dados de keystroke dynamics de uma submissão.

    Este endpoint permite salvar dados de keystroke dynamics durante a prova
    (a cada 2 minutos) ou ao finalizar. Os dados são concatenados se já existirem.

    Formato esperado dos dados (compatível com analyzer do Roberto):
    [
        {
            "key": "a",
            "timestamp": "2024-01-01 12:00:00.000",
            "application": "Browser",
            "flight_time": 0.123,  # tempo entre esta tecla e a anterior (ms)
            "hold_time": 0.056,    # tempo que a tecla ficou pressionada (ms)
            "command_type": null   # ou "paste", "copy", "cut", "backspace", "cursor_movement"
        },
        ...
    ]
    """
    aluno_repo = AlunoRepository(db)
    aluno = aluno_repo.get_by_email(current_user.email)
    if not aluno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado"
        )

    submissao_repo = SubmissaoRepository(db)
    submissao = submissao_repo.get_by_id(submissao_id)
    if not submissao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submissão não encontrada"
        )

    if submissao.aluno_id != aluno.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para atualizar esta submissão"
        )

    if submissao.keystroke_dynamics is None:
        submissao.keystroke_dynamics = keystroke_data
    else:
        submissao.keystroke_dynamics = submissao.keystroke_dynamics + keystroke_data

    db.commit()
    db.refresh(submissao)

    return {
        "message": "Keystroke dynamics salvos com sucesso",
        "total_events": len(submissao.keystroke_dynamics),
        "submissao_id": submissao_id
    }
