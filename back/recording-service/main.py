"""
Recording Service - Scalable Video Recording Microservice

Runs on separate port (8001 by default) to handle 100+ concurrent WebSocket connections.
Main API (port 8000) delegates recording tasks to this service.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
import app.models.professor_model # noqa: F401 - needed for Prova.professor relationship
import app.models.questao_model # noqa: F401 - needed for Prova.questoes relationship
from app.repositories.prova_repository import ProvaRepository
from app.repositories.aluno_repository import AlunoRepository

try:
    from app.core.firebase_config import auth as firebase_auth
except ImportError:
    print(" Warning: Firebase not configured. Authentication will fail.")
    firebase_auth = None

from config import config
from storage_manager import active_recordings

config.validate()

app = FastAPI(
    title="Recording Service",
    description="Scalable video recording service for exam platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "Recording Service",
        "status": "running",
        "active_recordings": active_recordings.get_active_count(),
        "max_concurrent": config.MAX_CONCURRENT_RECORDINGS
    }


@app.get("/health")
def health_check():
    """Health check endpoint for load balancers"""
    active_count = active_recordings.get_active_count()

    return {
        "status": "healthy",
        "active_recordings": active_count,
        "capacity_available": active_count < config.MAX_CONCURRENT_RECORDINGS,
        "capacity_percentage": (active_count / config.MAX_CONCURRENT_RECORDINGS) * 100
    }


@app.websocket("/ws/{prova_id}")
async def websocket_recording(websocket: WebSocket, prova_id: int):
    """
    WebSocket endpoint for receiving video streams.

    Protocol:
    1. Client sends: {"token": "JWT_TOKEN"}
    2. Server validates and responds: {"status": "authenticated", "aluno_id": 123, "prova_id": 456}
    3. Client sends video chunks as binary data
    4. Server saves to segments, supports resume if connection drops
    """
    await websocket.accept()

    if active_recordings.get_active_count() >= config.MAX_CONCURRENT_RECORDINGS:
        await websocket.send_text(json.dumps({
            "error": "Server at capacity. Please try again in a moment."
        }))
        await websocket.close()
        return

    db = SessionLocal()
    segment_manager = None

    try:
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)

        if auth_data.get("type") == "auth":
            token = auth_data.get("token")
        else:
            token = auth_data.get("token")

        if not token:
            await websocket.send_text(json.dumps({"error": "Token não fornecido"}))
            await websocket.close()
            return

        if not firebase_auth:
            await websocket.send_text(json.dumps({"error": "Firebase não configurado"}))
            await websocket.close()
            return

        try:
            decoded_token = firebase_auth.verify_id_token(token)
            email = decoded_token.get("email")
        except Exception as e:
            print(f" Token validation failed: {e}")
            await websocket.send_text(json.dumps({"error": "Token inválido"}))
            await websocket.close()
            return

        aluno_repo = AlunoRepository(db)
        aluno = aluno_repo.get_by_email(email)

        if not aluno:
            await websocket.send_text(json.dumps({"error": "Aluno não encontrado"}))
            await websocket.close()
            return

        prova_repo = ProvaRepository(db)
        prova = prova_repo.get_by_id(prova_id)

        if not prova:
            await websocket.send_text(json.dumps({"error": "Prova não encontrada"}))
            await websocket.close()
            return

        if aluno.email not in prova.emails_permitidos:
            await websocket.send_text(json.dumps({"error": "Sem permissão para esta prova"}))
            await websocket.close()
            return

        segment_manager = await active_recordings.start_recording(prova_id, aluno.id)

        await websocket.send_text(json.dumps({
            "status": "authenticated",
            "aluno_id": aluno.id,
            "prova_id": prova_id,
            "segment_index": segment_manager.current_segment_index,
            "message": f"Recording segment {segment_manager.current_segment_index} started"
        }))

        print(f" Recording started: prova={prova_id}, aluno={aluno.id}, segment={segment_manager.current_segment_index}")

        chunk_count = 0
        while True:
            try:
                data = await websocket.receive_bytes()
                segment_manager.write_chunk(data)
                chunk_count += 1

                if chunk_count % 100 == 0:
                    size_mb = segment_manager.get_total_size_mb()
                    print(f" Recording prova={prova_id}, aluno={aluno.id}: {chunk_count} chunks, {size_mb:.2f}MB")

            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f" Error receiving chunk: {e}")
                break

        print(f" Client disconnected: prova={prova_id}, aluno={aluno.id}")

    except Exception as e:
        print(f" WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass

    finally:
        db.close()

        if segment_manager:
            await active_recordings.pause_recording(prova_id, aluno.id)

        try:
            await websocket.close()
        except:
            pass


@app.post("/finalize/{prova_id}/{aluno_id}")
async def finalize_recording(prova_id: int, aluno_id: int):
    """
    Finalize recording and concatenate all segments.
    Called when:
    - Student finishes exam (finaliza prova)
    - Professor manually requests finalization

    Returns:
        Path to final concatenated video
    """
    final_file = await active_recordings.end_recording(
        prova_id,
        aluno_id,
        concatenate=True
    )

    if not final_file:
        raise HTTPException(404, "No active recording found")

    return {
        "message": "Recording finalized and concatenated",
        "file": str(final_file),
        "prova_id": prova_id,
        "aluno_id": aluno_id
    }


if __name__ == "__main__":
    import uvicorn

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║ Recording Service - Scalable Video Recording ║
║ ║
║ Status: Starting... ║
║ Port: {config.SERVICE_PORT} ║
║ Max Concurrent: {config.MAX_CONCURRENT_RECORDINGS} recordings ║
║ Storage: {config.RECORDINGS_DIR} ║
╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host=config.SERVICE_HOST,
        port=config.SERVICE_PORT,
        log_level="info",
        access_log=True
    )
