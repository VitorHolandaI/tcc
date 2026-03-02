from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import config

from app.core.database import Base as MainBase

Base = declarative_base()

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class KeystrokeAnalysis(Base):
    __tablename__ = "keystroke_analysis"

    id = Column(Integer, primary_key=True, index=True)
    prova_id = Column(Integer, nullable=False, index=True)
    aluno_id = Column(Integer, nullable=False, index=True)

    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(String, nullable=True)

    total_events = Column(Integer, nullable=True)
    hold_time_avg = Column(Float, nullable=True)
    hold_time_std = Column(Float, nullable=True)
    flight_time_avg = Column(Float, nullable=True)
    flight_time_std = Column(Float, nullable=True)

    command_counts = Column(JSON, nullable=True)  # {"paste": 5, "copy": 3, ...}
    suspicious_percentage = Column(Float, nullable=True)
    total_commands = Column(Integer, nullable=True)
    avg_manhattan_distance = Column(Float, nullable=True)
    command_sequences = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)


class SubmissaoReadOnly(MainBase):
    """
    Simplified read-only model for querying submissoes table.
    Uses MainBase to connect to the same table as the main app,
    but without relationships that would cause dependency issues.
    """
    __tablename__ = "submissoes"

    id = Column(Integer, primary_key=True, index=True)
    aluno_id = Column(Integer, nullable=False, index=True)
    prova_id = Column(Integer, nullable=False, index=True)
    questao_id = Column(Integer, nullable=False, index=True)
    codigo_submetido = Column(Text, nullable=False)
    keystroke_dynamics = Column(JSON, nullable=True)
    finalizada = Column(Boolean, default=False, nullable=False)
    data_envio = Column(DateTime, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)
