from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_current_path = Path(__file__).resolve()
_env_files = [
    str(_current_path.parents[3] / ".env") if len(_current_path.parents) > 3 else ".env",
    str(_current_path.parents[2] / ".env") if len(_current_path.parents) > 2 else ".env",
    ".env",
]

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://deepshield:changeme@postgres:5432/deepshield"
    REDIS_URL: str = "redis://redis:6379/0"
    JWT_SECRET: str = "super-secret-jwt-key-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7   # 7 days
    MODEL_PATH: str = "/models/deepshield_b4.pth"
    MODEL_BACKEND: str = "efficientnet"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=_env_files,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
