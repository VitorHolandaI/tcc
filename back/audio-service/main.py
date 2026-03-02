"""
Audio Service - Microservice for Audio Capture and Speaker Diarization
Port 8004
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth
import os
import asyncio
import sys
import json

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal as MainSessionLocal
from app.repositories.aluno_repository import AlunoRepository

from config import config
from database import get_db, AudioRecording, AudioAnalysis
from audio_analyzer import analyzer

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

app = FastAPI(
    title="Audio Service",
    description="Audio capture and speaker diarization microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config.AUDIO_DIR.mkdir(parents=True, exist_ok=True)


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


def get_audio_filename(prova_id: int, aluno_id: int) -> str:
    """Generate audio filename"""
    return f"prova_{prova_id}_aluno_{aluno_id}.wav"


@app.websocket("/ws/{prova_id}")
async def websocket_audio_capture(
    websocket: WebSocket,
    prova_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time audio capture.
    """
    await websocket.accept()

    aluno_id = None
    audio_file = None
    recording = None

    try:
        auth_msg = await websocket.receive_json()

        if auth_msg.get("type") != "auth":
            await websocket.send_json({"error": "First message must be auth"})
            await websocket.close()
            return

        token = auth_msg.get("token")
        if not token:
            await websocket.send_json({"error": "Missing token"})
            await websocket.close()
            return

        try:
            decoded = auth.verify_id_token(token)
            email = decoded.get("email")

            if not email:
                await websocket.send_json({"error": "Email not found in token"})
                await websocket.close()
                return

            main_db = MainSessionLocal()
            aluno_repo = AlunoRepository(main_db)
            aluno = aluno_repo.get_by_email(email)

            if not aluno:
                await websocket.send_json({"error": "Student not found in database"})
                main_db.close()
                await websocket.close()
                return

            aluno_id = aluno.id
            main_db.close()

        except Exception as e:
            await websocket.send_json({"error": f"Invalid token: {str(e)}"})
            await websocket.close()
            return

        filename = get_audio_filename(prova_id, aluno_id)
        audio_path = config.AUDIO_DIR / filename

        recording = AudioRecording(
            prova_id=prova_id,
            aluno_id=aluno_id,
            filename=filename,
            status="recording"
        )
        db.add(recording)
        db.commit()

        audio_file = open(audio_path, "wb")

        await websocket.send_json({
            "status": "authenticated",
            "message": "Ready to receive audio"
        })

        while True:
            try:
                data = await websocket.receive_bytes()

                audio_file.write(data)
                recording.file_size_bytes += len(data)

                if recording.file_size_bytes % 10000 == 0:
                    await websocket.send_json({
                        "status": "recording",
                        "bytes_received": recording.file_size_bytes
                    })

            except WebSocketDisconnect:
                break

    except Exception as e:
        print(f" Audio capture error: {e}")

        if recording:
            recording.status = "failed"
            db.commit()

        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass

    finally:
        if audio_file:
            audio_file.close()

        if recording:
            recording.status = "completed"
            recording.completed_at = datetime.now()
            db.commit()

        try:
            await websocket.close()
        except:
            pass

        print(f" Audio recording saved: prova={prova_id}, aluno={aluno_id}")


@app.get("/")
def root():
    """Health check"""
    return {
        "service": "Audio Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/analyze/{prova_id}/{aluno_id}")
async def start_audio_analysis(
    prova_id: int,
    aluno_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt_token)
):
    """
    Start speaker diarization analysis for audio.
    """
    if current_user.get("user_type") != "professor":
        raise HTTPException(403, "Only professors can request audio analysis")

    audio_path = config.AUDIO_DIR / get_audio_filename(prova_id, aluno_id)

    if not audio_path.exists():
        raise HTTPException(404, "Audio recording not found for this student")

    existing = db.query(AudioAnalysis).filter(
        AudioAnalysis.prova_id == prova_id,
        AudioAnalysis.aluno_id == aluno_id
    ).first()

    if existing and existing.status == "processing":
        return {
            "message": "Analysis already in progress",
            "status": "processing"
        }

    if existing:
        db.delete(existing)
        db.commit()

    analysis = AudioAnalysis(
        prova_id=prova_id,
        aluno_id=aluno_id,
        status="pending"
    )
    db.add(analysis)
    db.commit()

    background_tasks.add_task(
        run_audio_analysis,
        audio_path,
        prova_id,
        aluno_id
    )

    return {
        "message": "Audio analysis started in background",
        "status": "processing",
        "prova_id": prova_id,
        "aluno_id": aluno_id
    }


@app.get("/analysis/{prova_id}/{aluno_id}")
async def get_audio_analysis(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt_token)
):
    """
    Get audio analysis results.
    """
    if current_user.get("user_type") != "professor":
        raise HTTPException(403, "Only professors can view audio analysis")

    analysis = db.query(AudioAnalysis).filter(
        AudioAnalysis.prova_id == prova_id,
        AudioAnalysis.aluno_id == aluno_id
    ).first()

    if not analysis:
        return {
            "status": "not_found",
            "message": "No audio analysis requested yet"
        }

    if analysis.status == "processing":
        return {
            "status": "processing",
            "message": "Audio analysis in progress..."
        }

    if analysis.status == "failed":
        return {
            "status": "failed",
            "message": "Audio analysis failed",
            "error": analysis.error_message
        }

    speech_duration = 0
    if analysis.total_duration_seconds:
        speech_duration = analysis.total_duration_seconds * (1 - (analysis.silence_percentage / 100))

    return {
        "status": "completed",
        "prova_id": prova_id,
        "aluno_id": aluno_id,
        "results": {
            "total_speakers": analysis.total_speakers,
            "has_multiple_speakers": analysis.has_multiple_speakers,
            "total_duration_seconds": round(analysis.total_duration_seconds, 2),
            "silence_percentage": round(analysis.silence_percentage, 2),
            "speech_duration": round(speech_duration, 2)
        },
        "speaker_timeline": json.loads(analysis.speaker_timeline or "[]"),
        "multiple_speaker_periods": json.loads(analysis.multiple_speaker_periods or "[]"),
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
    }


def run_audio_analysis(audio_path: Path, prova_id: int, aluno_id: int):
    """
    Background task that runs speaker diarization.
    """
    from database import SessionLocal

    db = SessionLocal()

    try:
        print(f" Starting audio analysis: prova={prova_id}, aluno={aluno_id}")

        analyzer.analyze_audio(
            audio_path,
            prova_id,
            aluno_id,
            db
        )

        print(f" Audio analysis completed: prova={prova_id}, aluno={aluno_id}")

    except Exception as e:
        print(f" Audio analysis failed: {e}")

        analysis = db.query(AudioAnalysis).filter(
            AudioAnalysis.prova_id == prova_id,
            AudioAnalysis.aluno_id == aluno_id
        ).first()

        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    print(f" Starting Audio Service on {config.SERVICE_HOST}:{config.SERVICE_PORT}")

    uvicorn.run(
        "main:app",
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        reload=True
    )
