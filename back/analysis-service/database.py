"""
Database configuration for Analysis Service
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from config import config

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class VideoAnalysis(Base):
    """
    Video analysis results and progress tracking
    """
    __tablename__ = "video_analyses"

    id = Column(Integer, primary_key=True, index=True)

    prova_id = Column(Integer, nullable=False, index=True)
    aluno_id = Column(Integer, nullable=False, index=True)

    status = Column(String, default="pending", nullable=False)

    total_frames = Column(Integer, default=0)
    current_frame = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)

    percentage_forward = Column(Float, default=0.0)
    percentage_left = Column(Float, default=0.0)
    percentage_right = Column(Float, default=0.0)
    percentage_up = Column(Float, default=0.0)
    percentage_down = Column(Float, default=0.0)
    percentage_no_face = Column(Float, default=0.0)

    position_changes_per_minute = Column(Float, default=0.0)
    total_position_changes = Column(Integer, default=0)

    suspicious_periods = Column(Text, default="[]")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<VideoAnalysis prova={self.prova_id} aluno={self.aluno_id} status={self.status}>"


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
