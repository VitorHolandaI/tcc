from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.core.database import engine, Base
from app.controllers import prova_controller, professor_controller, aluno_controller, questao_controller, submissao_controller, monitoring_controller, recording_controller, avaliacao_controller
from app.core import firebase_config  # Initialize Firebase

if os.getenv("TESTING") != "true":
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="Escola API - Test Maker System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(professor_controller.router)
app.include_router(aluno_controller.router)
app.include_router(prova_controller.router)
app.include_router(questao_controller.router)
app.include_router(submissao_controller.router)
app.include_router(monitoring_controller.router)
app.include_router(recording_controller.router)
app.include_router(avaliacao_controller.router)


@app.get("/")
def root():
    return {"message": "API rodando! Acesse /docs para testar."}