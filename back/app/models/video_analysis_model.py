"""
Video Analysis Model - Simple TCC Version
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class VideoAnalysis(Base):
    """
    Análise de vídeo de gravação de prova.

    Relação 1:1 com (prova_id, aluno_id)
    """
    __tablename__ = "video_analyses"

    id = Column(Integer, primary_key=True, index=True)

    prova_id = Column(Integer, ForeignKey("provas.id"), nullable=False, index=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False, index=True)

    status = Column(String, default="pending", nullable=False)

    percentage_forward = Column(Float, default=0.0)      # Olhando para frente
    percentage_left = Column(Float, default=0.0)         # Olhando para esquerda
    percentage_right = Column(Float, default=0.0)        # Olhando para direita
    percentage_up = Column(Float, default=0.0)           # Olhando para cima
    percentage_down = Column(Float, default=0.0)         # Olhando para baixo
    percentage_no_face = Column(Float, default=0.0)      # Sem rosto detectado

    position_changes_per_minute = Column(Float, default=0.0)
    total_position_changes = Column(Integer, default=0)

    suspicious_periods = Column(Text, default="[]")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<VideoAnalysis prova={self.prova_id} aluno={self.aluno_id} status={self.status}>"
