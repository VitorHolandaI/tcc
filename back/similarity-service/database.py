from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import config

Base = declarative_base()
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class SimilarityAnalysis(Base):
    __tablename__ = "similarity_analysis"

    id = Column(Integer, primary_key=True, index=True)
    prova_id = Column(Integer, nullable=False, index=True, unique=True)

    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(String, nullable=True)

    results = Column(JSON, nullable=True)
    total_students = Column(Integer, nullable=True)
    total_flagged_pairs = Column(Integer, nullable=True)
    threshold_used = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
