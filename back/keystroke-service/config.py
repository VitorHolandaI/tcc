"""
Keystroke Analysis Service Configuration
Microservice for keystroke dynamics analysis
"""
import os
from pathlib import Path


class Config:
    """Configuration from environment variables"""

    SERVICE_HOST: str = os.getenv("KEYSTROKE_SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT: int = int(os.getenv("KEYSTROKE_SERVICE_PORT", "8005"))

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./keystroke_service.db"
    )

    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")

    MAX_CONCURRENT_ANALYSIS: int = int(os.getenv("MAX_CONCURRENT_KEYSTROKE_ANALYSIS", "5"))
    MIN_EVENTS_THRESHOLD: int = int(os.getenv("MIN_EVENTS_THRESHOLD", "10"))


config = Config()

