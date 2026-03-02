"""
Recording Controller - Main API

This controller only handles:
- Serving video files (GET)
- Checking recording status (GET)
- Deleting recordings (DELETE)
- Finalizing recordings (POST)

WebSocket recording is handled by the separate Recording Service (port 8001)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from pathlib import Path
import os
import httpx

from app.core.database import get_db
from app.core.auth_dependency import CurrentUser, get_current_professor
from app.repositories.prova_repository import ProvaRepository
from app.repositories.professor_repository import ProfessorRepository

router = APIRouter(prefix="/recordings", tags=["Gravações de Tela"])

DEFAULT_RECORDINGS_DIR = Path(__file__).parent.parent.parent / "recording-service" / "recordings"
RECORDINGS_DIR = Path(os.getenv("RECORDINGS_DIR", str(DEFAULT_RECORDINGS_DIR)))
RECORDINGS_DIR.mkdir(exist_ok=True, parents=True)

RECORDING_SERVICE_URL = os.getenv("RECORDING_SERVICE_URL", "http://localhost:8001")


def get_recording_filename(prova_id: int, aluno_id: int) -> str:
    """Gera nome padronizado para arquivo de gravação"""
    return f"prova_{prova_id}_aluno_{aluno_id}.webm"


@router.get("/video/{prova_id}/{aluno_id}")
async def get_recording(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Serve o arquivo de gravação de um aluno específico.

    SEGURANÇA:
    - Apenas professores podem acessar
    - Apenas o professor dono da prova pode ver gravações

    NOVO: Suporta streaming de vídeos em andamento
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
            detail="Você não tem permissão para acessar esta gravação"
        )

    filename = get_recording_filename(prova_id, aluno_id)
    file_path = RECORDINGS_DIR / filename

    if not file_path.exists():
        from pathlib import Path
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent / "recording-service"))

        try:
            from storage_manager import SegmentManager
            import asyncio

            base_filename = f"prova_{prova_id}_aluno_{aluno_id}"
            segments_dir = RECORDINGS_DIR / "segments" / base_filename

            if segments_dir.exists():
                print(f" Auto-concatenating segments for {base_filename}...")
                manager = SegmentManager(prova_id, aluno_id, base_recordings_dir=RECORDINGS_DIR)

                final_file = await manager.concatenate_segments()

                if not final_file or not Path(final_file).exists():
                    raise FileNotFoundError("Concatenation failed or returned an invalid path.")

                file_path = final_file
                print(f" Auto-concatenation successful: {file_path}")
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Gravação não encontrada. O aluno pode não ter gravado a tela."
                )
        except Exception as e:
            print(f" Error auto-concatenating: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gravação não encontrada ou erro ao processar: {str(e)}"
            )

    return FileResponse(
        path=file_path,
        media_type="video/webm",
        filename=filename,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Length, Content-Range, Accept-Ranges",
            "Cross-Origin-Resource-Policy": "cross-origin"
        }
    )


@router.get("/status/{prova_id}/{aluno_id}")
async def check_recording_exists(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Verifica se existe gravação para um aluno específico.
    Retorna informações básicas sem carregar o vídeo.

    NOVO: Também verifica se há gravação em andamento
    """
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(404, "Professor não encontrado")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)

    if not prova or prova.professor_id != professor.id:
        raise HTTPException(403, "Sem permissão")

    filename = get_recording_filename(prova_id, aluno_id)
    file_path = RECORDINGS_DIR / filename

    exists = file_path.exists()
    file_size = file_path.stat().st_size if exists else 0

    is_recording = False
    segment_count = 0

    try:
        async with httpx.AsyncClient() as client:
            segments_dir = RECORDINGS_DIR / "segments" / f"prova_{prova_id}_aluno_{aluno_id}"
            if segments_dir.exists():
                metadata_file = segments_dir / "metadata.json"
                if metadata_file.exists():
                    import json
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        segment_count = len(metadata.get("segments", []))
                        is_recording = True
    except Exception as e:
        print(f"Error checking recording status: {e}")

    return {
        "exists": exists,
        "filename": filename,
        "size_mb": round(file_size / (1024 * 1024), 2) if exists else 0,
        "is_recording": is_recording,
        "segment_count": segment_count,
        "status": "recording" if is_recording else ("finalized" if exists else "not_started"),
        "prova_id": prova_id,
        "aluno_id": aluno_id
    }


@router.post("/finalize/{prova_id}/{aluno_id}")
async def finalize_recording(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Finaliza uma gravação em andamento, concatenando todos os segments.

    Use cases:
    - Professor quer finalizar gravação de aluno que esqueceu de finalizar
    - Preparar vídeo para download enquanto prova ainda está em andamento
    """
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(404, "Professor não encontrado")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)

    if not prova or prova.professor_id != professor.id:
        raise HTTPException(403, "Sem permissão")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{RECORDING_SERVICE_URL}/finalize/{prova_id}/{aluno_id}",
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(404, "Nenhuma gravação ativa encontrada")
        raise HTTPException(500, f"Erro ao finalizar gravação: {e}")
    except Exception as e:
        raise HTTPException(500, f"Erro ao conectar ao serviço de gravação: {e}")


@router.delete("/video/{prova_id}/{aluno_id}")
async def delete_recording(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Deleta uma gravação (apenas professor dono da prova).
    Útil para economizar espaço em disco.

    NOVO: Também deleta segments se existirem
    """
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)

    if not professor:
        raise HTTPException(404, "Professor não encontrado")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)

    if not prova or prova.professor_id != professor.id:
        raise HTTPException(403, "Sem permissão")

    filename = get_recording_filename(prova_id, aluno_id)
    file_path = RECORDINGS_DIR / filename

    if not file_path.exists():
        raise HTTPException(404, "Gravação não encontrada")

    file_path.unlink()

    segments_dir = RECORDINGS_DIR / "segments" / f"prova_{prova_id}_aluno_{aluno_id}"
    if segments_dir.exists():
        import shutil
        shutil.rmtree(segments_dir)

    return {"message": "Gravação deletada com sucesso", "filename": filename}


@router.get("/service-health")
async def check_recording_service():
    """
    Verifica se o Recording Service está online.
    Útil para debugging e monitoramento.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RECORDING_SERVICE_URL}/health", timeout=5.0)
            response.raise_for_status()
            data = response.json()
            return {
                "status": "online",
                "recording_service": data
            }
    except Exception as e:
        return {
            "status": "offline",
            "error": str(e),
            "message": "Recording service is not available. Make sure it's running on port 8001."
        }


@router.get("/analyze/{prova_id}/{aluno_id}")
async def analyze_recording(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Analisa gravação para detectar gaze tracking (para onde aluno olhou).
    
    Returns:
        {
            "percentage_focused": float,
            "suspicious_periods": [...],
            "timeline": [...]
        }
    """
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)
    
    if not professor:
        raise HTTPException(404, "Professor não encontrado")
    
    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)
    
    if not prova or prova.professor_id != professor.id:
        raise HTTPException(403, "Sem permissão")
    
    filename = get_recording_filename(prova_id, aluno_id)
    file_path = RECORDINGS_DIR / filename

    if not file_path.exists():
        raise HTTPException(404, "Gravação não encontrada")

    from app.services.video_analysis_service import video_analysis_service
    
    try:
        analysis = video_analysis_service.analyze_video(file_path)
        return analysis
    except Exception as e:
        raise HTTPException(500, f"Erro ao analisar vídeo: {str(e)}")
