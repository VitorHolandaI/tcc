"""
Code Similarity Analysis Service Configuration
Microservice for detecting code plagiarism between student submissions
"""
import os


class Config:
    """Configuration from environment variables"""

    SERVICE_HOST: str = os.getenv("SIMILARITY_SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT: int = int(os.getenv("SIMILARITY_SERVICE_PORT", "8006"))

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./similarity_service.db"
    )

    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")

    MAX_CONCURRENT_ANALYSIS: int = int(os.getenv("MAX_CONCURRENT_SIMILARITY_ANALYSIS", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "70.0"))


config = Config()
