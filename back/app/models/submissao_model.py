from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Submissao(Base):
    __tablename__ = "submissoes"

    id = Column(Integer, primary_key=True, index=True)

    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False, index=True)
    prova_id = Column(Integer, ForeignKey("provas.id"), nullable=False, index=True)
    questao_id = Column(Integer, ForeignKey("questoes.id"), nullable=False, index=True)

    codigo_submetido = Column(Text, nullable=False)
    data_envio = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resultado_execucao = Column(Text, nullable=True)
    finalizada = Column(Boolean, default=False, nullable=False)
    nota = Column(Float, nullable=True)
    keystroke_dynamics = Column(JSON, nullable=True)  # Array de eventos de keystroke

    aluno = relationship("Aluno")
    prova = relationship("Prova")
    questao = relationship("Questao")

    __table_args__ = (
        UniqueConstraint('aluno_id', 'questao_id', name='_aluno_questao_uc'),
    )
