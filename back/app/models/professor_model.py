from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Professor(Base):
    __tablename__ = "professores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)

    provas = relationship("Prova", back_populates="professor", cascade="all, delete-orphan")
