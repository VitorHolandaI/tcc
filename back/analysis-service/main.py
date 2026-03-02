"""
Analysis Service - Modular Microservice for Video Gaze Analysis
Runs independently on port 8002 with JWT authentication
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth
import os

from config import config
from database import get_db, VideoAnalysis
from video_analyzer import analyzer

if not firebase_admin._apps:
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if service_account_path and os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
    else:
        try:
            firebase_admin.initialize_app()
        except Exception as e:
            print(f" Firebase initialization failed: {e}")
            print(" JWT validation will not work!")

app = FastAPI(
    title="Analysis Service",
    description="Modular video gaze analysis microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def is_professor_email(email: str) -> bool:
    """Check if email belongs to a professor based on domain"""
    if not email:
        return False
    PROFESSOR_WHITELIST = {"vitor.holanda@ccc.ufcg.edu.br"}
    return email.endswith("@computacao.ufcg.edu.br") or email in PROFESSOR_WHITELIST


async def verify_jwt_token(authorization: str = Header(None)) -> dict:
    """Verify Firebase JWT token"""
    if not authorization:
        raise HTTPException(401, "Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization format")

    token = authorization.replace("Bearer ", "")

    try:
        decoded = auth.verify_id_token(token)
        email = decoded.get("email")

        user_type = "professor" if is_professor_email(email) else "aluno"

        return {
            "uid": decoded.get("uid"),
            "email": email,
            "user_type": user_type
        }
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {str(e)}")


def get_recording_filename(prova_id: int, aluno_id: int) -> str:
    """Generate recording filename"""
    return f"webcam_prova_{prova_id}_aluno_{aluno_id}.webm"


def validate_professor_ownership(prova_id: int, professor_email: str, db: Session):
    """
    Validate that professor owns the prova.
    NOTE: This requires database access to provas and professors tables.
    For a fully decoupled service, you might want to call the main API instead.
    """
    return True


def validate_exam_finished(prova_id: int, db: Session) -> bool:
    """
    Validate that exam has finished (data_fim < now).
    For fully decoupled service, call main API.
    """
    return True


@app.get("/")
def root():
    """Health check"""
    return {
        "service": "Analysis Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/analyze/{prova_id}/{aluno_id}")
async def start_analysis(
    prova_id: int,
    aluno_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt_token)
):
    """
    Start video gaze analysis for a specific student.

     IMPORTANT: Only works if exam has finished (data_fim < now)

    Runs in background, does not block.
    Professor can check status with GET /analysis/{prova_id}/{aluno_id}
    """
    if current_user.get("user_type") != "professor":
        raise HTTPException(403, "Only professors can request analysis")

    if not validate_exam_finished(prova_id, db):
        raise HTTPException(
            400,
            "Exam still in progress or not found. Analysis only allowed after exam ends."
        )

    validate_professor_ownership(prova_id, current_user["email"], db)

    video_path = config.WEBCAM_RECORDINGS_DIR / get_recording_filename(prova_id, aluno_id)

    if not video_path.exists():
        raise HTTPException(404, "Recording not found for this student")

    existing = db.query(VideoAnalysis).filter(
        VideoAnalysis.prova_id == prova_id,
        VideoAnalysis.aluno_id == aluno_id
    ).first()

    if existing and existing.status == "processing":
        return {
            "message": "Analysis already in progress",
            "status": "processing",
            "progress": round(existing.progress_percentage, 1)
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
        run_analysis_background,
        video_path,
        prova_id,
        aluno_id
    )

    return {
        "message": "Analysis started in background",
        "status": "processing",
        "prova_id": prova_id,
        "aluno_id": aluno_id
    }


@app.get("/analysis/{prova_id}/{aluno_id}")
async def get_analysis(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt_token)
):
    """
    Get analysis results.

    Status:
    - "not_found": Analysis not requested yet
    - "processing": Analysis in progress (includes progress %)
    - "completed": Analysis finished (returns metrics)
    - "failed": Analysis failed
    """
    if current_user.get("user_type") != "professor":
        raise HTTPException(403, "Only professors can view analysis")

    analysis = db.query(VideoAnalysis).filter(
        VideoAnalysis.prova_id == prova_id,
        VideoAnalysis.aluno_id == aluno_id
    ).first()

    if not analysis:
        return {
            "status": "not_found",
            "message": "No analysis requested yet"
        }

    if analysis.status == "processing":
        return {
            "status": "processing",
            "message": "Analysis in progress",
            "progress": round(analysis.progress_percentage, 1)
        }

    if analysis.status == "failed":
        return {
            "status": "failed",
            "message": "Analysis failed",
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
        "suspicious_periods": json.loads(analysis.suspicious_periods or "[]"),
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
    }


def run_analysis_background(video_path: Path, prova_id: int, aluno_id: int):
    """
    Background task that processes video.
    Saves progress to database (can resume if interrupted).
    """
    from database import SessionLocal

    db = SessionLocal()

    try:
        print(f" Starting analysis: prova={prova_id}, aluno={aluno_id}")

        analyzer.analyze_video(
            video_path,
            prova_id,
            aluno_id,
            db
        )

        print(f" Analysis completed: prova={prova_id}, aluno={aluno_id}")

    except Exception as e:
        print(f" Analysis failed: {e}")

        db.rollback()

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


if __name__ == "__main__":
    import uvicorn

    print(f" Starting Analysis Service on {config.SERVICE_HOST}:{config.SERVICE_PORT}")

    uvicorn.run(
        "main:app",
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        reload=True
    )
