from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Questao(Base):
    __tablename__ = "questoes"

    id = Column(Integer, primary_key=True, index=True)
    prova_id = Column(Integer, ForeignKey("provas.id"), nullable=False, index=True)
    titulo = Column(String, nullable=False)
    descricao = Column(String, nullable=False)
    exemplo_input1 = Column(String, nullable=False)
    exemplo_output1 = Column(String, nullable=False)
    exemplo_input2 = Column(String, nullable=True)
    exemplo_output2 = Column(String, nullable=True)
    peso = Column(Float, nullable=False, default=1.0)

    prova = relationship("Prova", back_populates="questoes")
