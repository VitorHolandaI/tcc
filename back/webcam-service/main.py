"""
Webcam Service - Microservice for Webcam Video Capture
Port 8003
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, auth
import os
import sys
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, get_db
from app.repositories.aluno_repository import AlunoRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.professor_repository import ProfessorRepository
from app.core.auth_dependency import CurrentUser, get_current_professor

import app.models.professor_model
import app.models.questao_model


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
    title="Webcam Service",
    description="Webcam video capture microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEBCAM_DIR = Path(os.getenv("WEBCAM_DIR", "./webcam_recordings"))
WEBCAM_DIR.mkdir(parents=True, exist_ok=True)


def get_webcam_filename(prova_id: int, aluno_id: int) -> str:
    """Generate webcam filename"""
    return f"webcam_prova_{prova_id}_aluno_{aluno_id}.webm"


@app.get("/")
def root():
    """Health check"""
    return {
        "service": "Webcam Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.websocket("/ws/{prova_id}")
async def websocket_webcam_capture(
    websocket: WebSocket,
    prova_id: int
):
    """
    WebSocket endpoint for webcam video capture.

    Client should send:
    1. Authentication message: {"type": "auth", "token": "JWT_TOKEN"}
    2. Video chunks: binary data
    3. Close when done
    """
    await websocket.accept()

    aluno_id = None
    video_file = None

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

            db = SessionLocal()
            aluno_repo = AlunoRepository(db)
            aluno = aluno_repo.get_by_email(email)

            if not aluno:
                await websocket.send_json({"error": "Student not found in database"})
                db.close()
                await websocket.close()
                return

            aluno_id = aluno.id
            db.close()

        except Exception as e:
            await websocket.send_json({"error": f"Invalid token: {str(e)}"})
            await websocket.close()
            return

        filename = get_webcam_filename(prova_id, aluno_id)
        video_path = WEBCAM_DIR / filename

        video_file = open(video_path, "wb")

        await websocket.send_json({
            "status": "authenticated",
            "message": "Ready to receive webcam video"
        })

        print(f" Webcam recording started: prova={prova_id}, aluno={aluno_id}")

        bytes_received = 0

        while True:
            try:
                data = await websocket.receive_bytes()
                video_file.write(data)
                bytes_received += len(data)

                if bytes_received % 100000 < 10000:
                    await websocket.send_json({
                        "status": "recording",
                        "bytes_received": bytes_received
                    })

            except WebSocketDisconnect:
                break

    except Exception as e:
        print(f" Webcam capture error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass

    finally:
        if video_file:
            video_file.close()

        try:
            await websocket.close()
        except:
            pass

        print(f" Webcam recording saved: prova={prova_id}, aluno={aluno_id}")


@app.get("/video/{prova_id}/{aluno_id}")
async def get_webcam_recording(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_professor)
):
    """
    Serve o arquivo de gravação da webcam de um aluno específico.
    Acesso restrito ao professor dono da prova.
    """
    prof_repo = ProfessorRepository(db)
    professor = prof_repo.get_by_email(current_user.email)
    if not professor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Professor não encontrado")

    prova_repo = ProvaRepository(db)
    prova = prova_repo.get_by_id(prova_id)
    if not prova:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Prova não encontrada")

    if prova.professor_id != professor.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Você não tem permissão para acessar esta gravação")

    filename = get_webcam_filename(prova_id, aluno_id)
    file_path = WEBCAM_DIR / filename

    if not file_path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gravação da webcam não encontrada.")

    return FileResponse(
        path=file_path,
        media_type="video/webm",
        filename=filename,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
        }
    )


if __name__ == "__main__":
    import uvicorn

    print(" Starting Webcam Service on port 8003")
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
