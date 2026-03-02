from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.enums import LinguagemEnum

class Prova(Base):
    __tablename__ = "provas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False, index=True)
    descricao = Column(String, nullable=True)
    data_aplicacao = Column(String, nullable=False)
    data_fim = Column(String, nullable=False)

    professor_id = Column(Integer, ForeignKey("professores.id"), nullable=False, index=True)
    linguagem = Column(SQLEnum(LinguagemEnum), nullable=False)
    emails_permitidos = Column(JSON, nullable=True, default=[])  # Lista de emails de alunos permitidos
    max_saidas = Column(Integer, nullable=False, default=3)  # Número máximo de saídas permitidas da página da prova

    professor = relationship("Professor", back_populates="provas")
    questoes = relationship("Questao", back_populates="prova", cascade="all, delete-orphan")
