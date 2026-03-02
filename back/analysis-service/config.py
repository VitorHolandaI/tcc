"""
Analysis Service Configuration
Modular container for video gaze analysis
"""
import os
from pathlib import Path


class Config:
    """Configuration from environment variables"""

    SERVICE_HOST: str = os.getenv("ANALYSIS_SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT: int = int(os.getenv("ANALYSIS_SERVICE_PORT", "8002"))

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./analysis_service.db"
    )

    WEBCAM_RECORDINGS_DIR: Path = Path(os.getenv("WEBCAM_RECORDINGS_DIR", "../webcam-service/webcam_recordings/"))

    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")

    MAX_CONCURRENT_ANALYSIS: int = int(os.getenv("MAX_CONCURRENT_ANALYSIS", "10"))
    PROCESS_EVERY_N_FRAMES: int = int(os.getenv("PROCESS_EVERY_N_FRAMES", "5"))

    USE_GPU: bool = os.getenv("USE_GPU", "false").lower() == "true"


config = Config()
