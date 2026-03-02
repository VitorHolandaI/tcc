"""
Database configuration for Audio Service
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from config import config

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AudioRecording(Base):
    """
    Audio recording metadata
    """
    __tablename__ = "audio_recordings"

    id = Column(Integer, primary_key=True, index=True)

    prova_id = Column(Integer, nullable=False, index=True)
    aluno_id = Column(Integer, nullable=False, index=True)

    filename = Column(String, nullable=False)
    duration_seconds = Column(Float, default=0.0)
    file_size_bytes = Column(Integer, default=0)

    status = Column(String, default="recording", nullable=False)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AudioRecording prova={self.prova_id} aluno={self.aluno_id} status={self.status}>"


class AudioAnalysis(Base):
    """
    Audio speaker diarization analysis results
    """
    __tablename__ = "audio_analyses"

    id = Column(Integer, primary_key=True, index=True)

    prova_id = Column(Integer, nullable=False, index=True)
    aluno_id = Column(Integer, nullable=False, index=True)

    status = Column(String, default="pending", nullable=False)

    total_speakers = Column(Integer, default=0)
    has_multiple_speakers = Column(Boolean, default=False)

    #   {"start": 0.0, "end": 15.3, "speaker": "SPEAKER_00"},
    #   {"start": 15.3, "end": 28.7, "speaker": "SPEAKER_01"},
    #   {"start": 28.7, "end": 45.2, "speaker": "SPEAKER_00"}
    # ]
    speaker_timeline = Column(Text, default="[]")

    #   {"start": 120.5, "end": 145.2, "duration": 24.7, "speakers": ["SPEAKER_00", "SPEAKER_01"]}
    # ]
    multiple_speaker_periods = Column(Text, default="[]")

    total_duration_seconds = Column(Float, default=0.0)
    silence_percentage = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AudioAnalysis prova={self.prova_id} aluno={self.aluno_id} speakers={self.total_speakers}>"


def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
