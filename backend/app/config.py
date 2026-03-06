from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379"
    MAX_FILE_SIZE_MB: int = 50
    CODE_TTL_SECONDS: int = 600
    ALLOWED_EXTENSIONS: List[str] = [
        "txt", "pdf", "docx", "doc", "png", "jpg", "jpeg",
        "gif", "webp", "apk", "zip", "csv", "xlsx", "xls", "mp4", "mp3"
    ]
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW: int = 60
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    FRONTEND_URL: str = ""
    UPLOAD_DIR: str = "/tmp/quickshare"

    class Config:
        env_file = ".env"


settings = Settings()
