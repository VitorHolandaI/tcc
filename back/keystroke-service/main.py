from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, auth
import os
import sys
import json
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal as MainSessionLocal
from database import get_db, KeystrokeAnalysis, SubmissaoReadOnly
from analyzer import KeyloggerAnalyzer
from config import config

if not firebase_admin._apps:
    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if service_account_path and os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
    else:
        try:
            firebase_admin.initialize_app()
        except Exception as e:
            print(f"Warning: Firebase initialization failed: {e}")

app = FastAPI(
    title="Keystroke Analysis Service",
    description="Analise de keystroke dynamics para deteccao de comportamento suspeito",
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

@app.get("/")
def root():
    return {
        "service": "Keystroke Analysis Service",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/analyze/{prova_id}/{aluno_id}")
async def start_keystroke_analysis(
    prova_id: int,
    aluno_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt_token)
):
    if current_user.get("user_type") != "professor":
        raise HTTPException(403, "Only professors can request keystroke analysis")

    main_db = MainSessionLocal()
    try:
        submissao = main_db.query(SubmissaoReadOnly).filter(
            SubmissaoReadOnly.prova_id == prova_id,
            SubmissaoReadOnly.aluno_id == aluno_id
        ).first()

        if not submissao:
            raise HTTPException(404, "Submissao nao encontrada")

        if not submissao.keystroke_dynamics:
            raise HTTPException(404, "Keystroke data nao disponivel")

        existing = db.query(KeystrokeAnalysis).filter(
            KeystrokeAnalysis.prova_id == prova_id,
            KeystrokeAnalysis.aluno_id == aluno_id
        ).first()

        if existing and existing.status == "processing":
            return {
                "message": "Analysis already in progress",
                "status": "processing"
            }

        if existing:
            db.delete(existing)
            db.commit()

        analysis = KeystrokeAnalysis(
            prova_id=prova_id,
            aluno_id=aluno_id,
            status="pending"
        )
        db.add(analysis)
        db.commit()

        background_tasks.add_task(
            run_keystroke_analysis,
            submissao.keystroke_dynamics,
            prova_id,
            aluno_id
        )

        return {
            "message": "Keystroke analysis started in background",
            "status": "processing",
            "total_events": len(submissao.keystroke_dynamics)
        }

    finally:
        main_db.close()

@app.get("/analysis/{prova_id}/{aluno_id}")
async def get_keystroke_analysis(
    prova_id: int,
    aluno_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt_token)
):
    if current_user.get("user_type") != "professor":
        raise HTTPException(403, "Only professors can view keystroke analysis")

    analysis = db.query(KeystrokeAnalysis).filter(
        KeystrokeAnalysis.prova_id == prova_id,
        KeystrokeAnalysis.aluno_id == aluno_id
    ).first()

    if not analysis:
        return {
            "status": "not_found",
            "message": "No keystroke analysis requested yet"
        }

    if analysis.status == "processing":
        return {
            "status": "processing",
            "message": "Keystroke analysis in progress..."
        }

    if analysis.status == "failed":
        return {
            "status": "failed",
            "message": "Keystroke analysis failed",
            "error": analysis.error_message
        }

    return {
        "status": "completed",
        "prova_id": prova_id,
        "aluno_id": aluno_id,
        "typing_metrics": {
            "total_events": analysis.total_events,
            "hold_time_avg": analysis.hold_time_avg,
            "hold_time_std": analysis.hold_time_std,
            "flight_time_avg": analysis.flight_time_avg,
            "flight_time_std": analysis.flight_time_std
        },
        "suspicious_commands": {
            "command_counts": analysis.command_counts,
            "suspicious_percentage": analysis.suspicious_percentage,
            "total_commands": analysis.total_commands,
            "avg_manhattan_distance": analysis.avg_manhattan_distance,
            "command_sequences": analysis.command_sequences
        },
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
    }

def run_keystroke_analysis(keystroke_data: list, prova_id: int, aluno_id: int):
    from database import SessionLocal

    db = SessionLocal()
    try:
        print(f"Starting keystroke analysis: prova={prova_id}, aluno={aluno_id}")

        analysis = db.query(KeystrokeAnalysis).filter(
            KeystrokeAnalysis.prova_id == prova_id,
            KeystrokeAnalysis.aluno_id == aluno_id
        ).first()

        if analysis:
            analysis.status = "processing"
            db.commit()

        temp_file = f"/tmp/keystroke_prova_{prova_id}_aluno_{aluno_id}.json"
        with open(temp_file, 'w') as f:
            json.dump(keystroke_data, f, indent=4)

        analyzer = KeyloggerAnalyzer(temp_file)
        typing_metrics = analyzer.calculate_typing_metrics()
        suspicious_commands = analyzer.analyze_suspicious_commands()

        if analysis:
            analysis.status = "completed"
            analysis.total_events = typing_metrics["total_events"]
            analysis.hold_time_avg = typing_metrics["hold_time_avg"]
            analysis.hold_time_std = typing_metrics["hold_time_std"]
            analysis.flight_time_avg = typing_metrics["flight_time_avg"]
            analysis.flight_time_std = typing_metrics["flight_time_std"]
            analysis.command_counts = suspicious_commands["command_counts"]
            analysis.suspicious_percentage = suspicious_commands["suspicious_percentage"]
            analysis.total_commands = suspicious_commands["total_commands"]
            analysis.avg_manhattan_distance = suspicious_commands["avg_manhattan_distance"]
            analysis.command_sequences = suspicious_commands["command_sequences"]
            analysis.completed_at = datetime.now()
            db.commit()

        print(f"Keystroke analysis completed: prova={prova_id}, aluno={aluno_id}")
        print(f"   - Total events: {typing_metrics['total_events']}")
        print(f"   - Suspicious %: {suspicious_commands['suspicious_percentage']}%")

        os.remove(temp_file)

    except Exception as e:
        print(f"Keystroke analysis failed: {e}")
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    print(f"Starting Keystroke Analysis Service on port {config.SERVICE_PORT}")
    uvicorn.run("main:app", host=config.SERVICE_HOST, port=config.SERVICE_PORT, reload=True)
