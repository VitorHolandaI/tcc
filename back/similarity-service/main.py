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
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal as MainSessionLocal
from app.models.submissao_model import Submissao
from app.models.questao_model import Questao
from app.models.aluno_model import Aluno
from app.models.prova_model import Prova
from app.models.professor_model import Professor
from database import get_db, SimilarityAnalysis
from analyzer import CodeSimilarityAnalyzer
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
    title="Code Similarity Analysis Service",
    description="Analise de similaridade de codigo entre submissoes de alunos",
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


def verify_professor_owns_prova(email: str, prova_id: int, main_db) -> bool:
    """Verify that the professor owns the prova."""
    professor = main_db.query(Professor).filter(Professor.email == email).first()
    if not professor:
        return False
    prova = main_db.query(Prova).filter(Prova.id == prova_id).first()
    if not prova:
        return False
    return prova.professor_id == professor.id


@app.get("/")
def root():
    return {
        "service": "Code Similarity Analysis Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/analyze/{prova_id}")
async def start_similarity_analysis(
    prova_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt_token)
):
    """Start code similarity analysis for all submissions in a prova."""
    main_db = MainSessionLocal()
    try:
        if not verify_professor_owns_prova(current_user["email"], prova_id, main_db):
            raise HTTPException(403, "Voce nao tem permissao para analisar esta prova")

        prova = main_db.query(Prova).filter(Prova.id == prova_id).first()
        if not prova:
            raise HTTPException(404, "Prova nao encontrada")

        submissions = main_db.query(Submissao).filter(
            Submissao.prova_id == prova_id
        ).all()

        if not submissions:
            raise HTTPException(404, "Nenhuma submissao encontrada para esta prova")

        existing = db.query(SimilarityAnalysis).filter(
            SimilarityAnalysis.prova_id == prova_id
        ).first()

        if existing and existing.status == "processing":
            return {
                "message": "Analise ja em andamento",
                "status": "processing"
            }

        if existing:
            db.delete(existing)
            db.commit()

        analysis = SimilarityAnalysis(
            prova_id=prova_id,
            status="pending"
        )
        db.add(analysis)
        db.commit()

        submissions_data = []
        for sub in submissions:
            aluno = main_db.query(Aluno).filter(Aluno.id == sub.aluno_id).first()
            submissions_data.append({
                "aluno_id": sub.aluno_id,
                "aluno_nome": aluno.nome if aluno else f"Aluno {sub.aluno_id}",
                "aluno_email": aluno.email if aluno else "",
                "questao_id": sub.questao_id,
                "codigo_submetido": sub.codigo_submetido or ""
            })

        questoes = main_db.query(Questao).filter(Questao.prova_id == prova_id).all()
        question_titles = {q.id: q.titulo for q in questoes}

        background_tasks.add_task(
            run_similarity_analysis,
            prova_id,
            submissions_data,
            question_titles,
            prova.linguagem
        )

        return {
            "message": "Analise de similaridade iniciada",
            "status": "processing",
            "total_submissions": len(submissions)
        }

    finally:
        main_db.close()


@app.get("/analysis/{prova_id}")
async def get_similarity_analysis(
    prova_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_jwt_token)
):
    """Get code similarity analysis results for a prova."""
    main_db = MainSessionLocal()
    try:
        if not verify_professor_owns_prova(current_user["email"], prova_id, main_db):
            raise HTTPException(403, "Voce nao tem permissao para ver esta analise")
    finally:
        main_db.close()

    analysis = db.query(SimilarityAnalysis).filter(
        SimilarityAnalysis.prova_id == prova_id
    ).first()

    if not analysis:
        return {
            "status": "not_found",
            "message": "Nenhuma analise de similaridade solicitada ainda"
        }

    if analysis.status == "processing":
        return {
            "status": "processing",
            "message": "Analise de similaridade em andamento..."
        }

    if analysis.status == "failed":
        return {
            "status": "failed",
            "message": "Analise de similaridade falhou",
            "error": analysis.error_message
        }

    return {
        "status": "completed",
        "prova_id": prova_id,
        "total_students": analysis.total_students,
        "total_flagged_pairs": analysis.total_flagged_pairs,
        "threshold_used": analysis.threshold_used,
        "questions": analysis.results,
        "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None
    }


def run_similarity_analysis(
    prova_id: int,
    submissions_data: list,
    question_titles: dict,
    language: str
):
    """Background task to run code similarity analysis."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        print(f"Starting similarity analysis: prova={prova_id}")

        analysis = db.query(SimilarityAnalysis).filter(
            SimilarityAnalysis.prova_id == prova_id
        ).first()

        if analysis:
            analysis.status = "processing"
            db.commit()

        submissions_by_question = defaultdict(list)
        for sub in submissions_data:
            submissions_by_question[sub["questao_id"]].append(sub)

        analyzer = CodeSimilarityAnalyzer(language=language)
        results = analyzer.analyze_prova(
            submissions_by_question=dict(submissions_by_question),
            question_titles=question_titles,
            threshold=config.SIMILARITY_THRESHOLD
        )

        if analysis:
            analysis.status = "completed"
            analysis.results = results["questions"]
            analysis.total_students = results["total_students"]
            analysis.total_flagged_pairs = results["total_flagged_pairs"]
            analysis.threshold_used = results["threshold_used"]
            analysis.completed_at = datetime.now()
            db.commit()

        print(f"Similarity analysis completed: prova={prova_id}")
        print(f"   - Total students: {results['total_students']}")
        print(f"   - Flagged pairs: {results['total_flagged_pairs']}")

    except Exception as e:
        print(f"Similarity analysis failed: {e}")
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    print(f"Starting Code Similarity Analysis Service on port {config.SERVICE_PORT}")
    uvicorn.run("main:app", host=config.SERVICE_HOST, port=config.SERVICE_PORT, reload=True)
