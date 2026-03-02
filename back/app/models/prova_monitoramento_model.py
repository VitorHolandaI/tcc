from sqlalchemy import Column, Integer, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProvaMonitoramento(Base):
    """
    Modelo para monitorar a atividade do aluno durante a prova.
    Registra quantas vezes o aluno saiu da página da prova e se a prova foi invalidada.
    """
    __tablename__ = "provas_monitoramento"

    id = Column(Integer, primary_key=True, index=True)

    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False, index=True)
    prova_id = Column(Integer, ForeignKey("provas.id"), nullable=False, index=True)

    numero_saidas = Column(Integer, default=0, nullable=False)  # Quantas vezes o aluno saiu da página
    invalidada = Column(Boolean, default=False, nullable=False)  # Se a prova foi invalidada por excesso de saídas

    aluno = relationship("Aluno")
    prova = relationship("Prova")

    __table_args__ = (
        UniqueConstraint('aluno_id', 'prova_id', name='_aluno_prova_monitoramento_uc'),
    )
