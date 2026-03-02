"""
Audio Service Configuration
Microservice for audio capture and speaker diarization
"""
import os
from pathlib import Path


class Config:
    """Configuration from environment variables"""

    SERVICE_HOST: str = os.getenv("AUDIO_SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT: int = int(os.getenv("AUDIO_SERVICE_PORT", "8004"))

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./audio_service.db"
    )

    AUDIO_DIR: Path = Path(os.getenv("AUDIO_DIR", "./audio_recordings"))

    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")

    HUGGINGFACE_TOKEN: str = os.getenv("HUGGINGFACE_TOKEN", "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")
    USE_GPU: bool = os.getenv("USE_GPU", "false").lower() == "true"

    MAX_CONCURRENT_ANALYSIS: int = int(os.getenv("MAX_CONCURRENT_AUDIO_ANALYSIS", "5"))
    MIN_SPEAKER_CONFIDENCE: float = float(os.getenv("MIN_SPEAKER_CONFIDENCE", "0.5"))


config = Config()
