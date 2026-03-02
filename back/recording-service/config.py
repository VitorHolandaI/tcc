"""
Recording Service Configuration
Scalable video recording service with environment variables
"""
import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuration class using environment variables"""

    SERVICE_HOST: str = os.getenv("RECORDING_SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT: int = int(os.getenv("RECORDING_SERVICE_PORT", "8001"))

    RECORDINGS_DIR: Path = Path(os.getenv("RECORDINGS_DIR", "./recordings"))
    SEGMENTS_DIR: Path = Path(os.getenv("SEGMENTS_DIR", "./recordings/segments"))
    MAX_SEGMENT_SIZE_MB: int = int(os.getenv("MAX_SEGMENT_SIZE_MB", "50"))

    MAIN_API_URL: str = os.getenv("MAIN_API_URL", "http://localhost:8000")

    FIREBASE_CREDENTIALS_PATH: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH")

    MAX_CONCURRENT_RECORDINGS: int = int(os.getenv("MAX_CONCURRENT_RECORDINGS", "150"))
    CHUNK_DURATION_MS: int = int(os.getenv("CHUNK_DURATION_MS", "1000"))

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./escola.db")

    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

    AUTO_DELETE_DAYS: int = int(os.getenv("AUTO_DELETE_RECORDINGS_DAYS", "30"))

    @classmethod
    def init_directories(cls):
        """Create necessary directories"""
        cls.RECORDINGS_DIR.mkdir(exist_ok=True, parents=True)
        cls.SEGMENTS_DIR.mkdir(exist_ok=True, parents=True)

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.MAX_CONCURRENT_RECORDINGS < 1:
            raise ValueError("MAX_CONCURRENT_RECORDINGS must be >= 1")

        if cls.MAX_SEGMENT_SIZE_MB < 10:
            raise ValueError("MAX_SEGMENT_SIZE_MB must be >= 10")

        cls.init_directories()

        print(f" Recording Service Configuration:")
        print(f" - Host: {cls.SERVICE_HOST}:{cls.SERVICE_PORT}")
        print(f" - Storage: {cls.RECORDINGS_DIR.absolute()}")
        print(f" - Max Concurrent: {cls.MAX_CONCURRENT_RECORDINGS}")
        print(f" - Main API: {cls.MAIN_API_URL}")
        print(f" - Redis: {cls.REDIS_URL or 'Not configured (single instance)'}")

config = Config()
