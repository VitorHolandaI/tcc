"""
Analysis Controller - Simplified for TCC
Simple gaze analysis after exam finishes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import os

from app.core.database import get_db
from app.core.auth_dependency import CurrentUser, get_current_professor
from app.repositories.prova_repository import ProvaRepository
from app.repositories.professor_repository import ProfessorRepository
from app.models.video_analysis_model import VideoAnalysis
from app.services.video_analysis_service import video_analysis_service

router = APIRouter(prefix="/analysis", tags=["Análise de Vídeos"])

RECORDINGS_DIR = Path(os.getenv("RECORDINGS_DIR", "./recordings"))


def get_recording_filename(prova_id: int, aluno_id: int) -> str:
    return f"prova_{prova_id}_aluno_{aluno_id}.webm"


@router.post("/analyze/{prova_id}/{aluno_id}")
async def analyze_recording(
    prova_id: int,
    aluno_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Inicia análise de gaze de um aluno específico.

     IMPORTANTE: Só funciona se prova já terminou (data_fim < agora)

    Roda em background, não bloqueia.
    Professor pode consultar resultado com GET /analysis/{prova_id}/{aluno_id}
    """
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(404, "Professor não encontrado")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)

    if not prova:
        raise HTTPException(404, "Prova não encontrada")

    if prova.professor_id != professor.id:
        raise HTTPException(403, "Sem permissão para esta prova")

    now = datetime.now()
    data_fim = datetime.fromisoformat(prova.data_fim.replace('Z', '+00:00')) if isinstance(prova.data_fim, str) else prova.data_fim

    if data_fim > now:
        raise HTTPException(
            400,
            f"Prova ainda em andamento. Término previsto: {data_fim.strftime('%d/%m/%Y %H:%M')}"
        )

    video_path = RECORDINGS_DIR / get_recording_filename(prova_id, aluno_id)

    if not video_path.exists():
        raise HTTPException(404, "Gravação não encontrada para este aluno")

    existing = db.query(VideoAnalysis).filter(
        VideoAnalysis.prova_id == prova_id,
        VideoAnalysis.aluno_id == aluno_id
    ).first()

    if existing and existing.status == "processing":
        return {
            "message": "Análise já está em andamento",
            "status": "processing"
        }

    if existing:
        db.delete(existing)
        db.commit()

    analysis = VideoAnalysis(
        prova_id=prova_id,
        aluno_id=aluno_id,
        status="pending"
    )
    db.add(analysis)
    db.commit()

    background_tasks.add_task(
        run_analysis,
        video_path,
        prova_id,
        aluno_id
    )

    return {
        "message": "Análise iniciada em background",
        "status": "processing",
        "prova_id": prova_id,
        "aluno_id": aluno_id
    }


def run_analysis(video_path: Path, prova_id: int, aluno_id: int):
    """
    Função que roda em background.
    Processa vídeo e salva resultado no banco.
    """
    from app.core.database import SessionLocal

    db = SessionLocal()

    try:
        print(f" Iniciando análise: prova={prova_id}, aluno={aluno_id}")

        video_analysis_service.analyze_video_with_progress(
            video_path,
            prova_id,
            aluno_id,
            db
        )

        print(f" Análise concluída: prova={prova_id}, aluno={aluno_id}")

    except Exception as e:
        print(f" Erro na análise: {e}")

        analysis = db.query(VideoAnalysis).filter(
            VideoAnalysis.prova_id == prova_id,
            VideoAnalysis.aluno_id == aluno_id
        ).first()

        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()

    finally:
        db.close()


@router.get("/{prova_id}/{aluno_id}")
async def get_analysis(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Retorna resultado da análise de gaze.

    Status possíveis:
    - "not_found": Análise ainda não foi solicitada
    - "processing": Análise em andamento
    - "completed": Análise concluída (retorna métricas)
    - "failed": Análise falhou
    """
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(404, "Professor não encontrado")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)

    if not prova or prova.professor_id != professor.id:
        raise HTTPException(403, "Sem permissão")

    analysis = db.query(VideoAnalysis).filter(
        VideoAnalysis.prova_id == prova_id,
        VideoAnalysis.aluno_id == aluno_id
    ).first()

    if not analysis:
        return {
            "status": "not_found",
            "message": "Nenhuma análise foi solicitada ainda"
        }

    if analysis.status == "processing":
        return {
            "status": "processing",
            "message": "Análise em andamento..."
        }

    if analysis.status == "failed":
        return {
            "status": "failed",
            "message": "Análise falhou",
            "error": analysis.error_message
        }

    import json

    return {
        "status": "completed",
        "prova_id": prova_id,
        "aluno_id": aluno_id,
        "metrics": {
            "percentage_forward": round(analysis.percentage_forward, 1),
            "percentage_left": round(analysis.percentage_left, 1),
            "percentage_right": round(analysis.percentage_right, 1),
            "percentage_up": round(analysis.percentage_up, 1),
            "percentage_down": round(analysis.percentage_down, 1),
            "percentage_no_face": round(analysis.percentage_no_face, 1),
            "position_changes_per_minute": round(analysis.position_changes_per_minute, 1),
            "total_position_changes": analysis.total_position_changes
        },
        "suspicious_periods": json.loads(analysis.suspicious_periods),
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
    }
