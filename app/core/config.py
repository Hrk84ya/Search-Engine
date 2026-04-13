"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://searchuser:searchpass@localhost:5432/semantic_search"
    sync_database_url: str = "postgresql://searchuser:searchpass@localhost:5432/semantic_search"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ML Models
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "google/flan-t5-large"
    embedding_dimension: int = 384

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"

    # Chunking
    chunk_size: int = 200
    chunk_overlap: int = 30

    # Retrieval
    top_k: int = 5

    # Auth
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60

    # App
    upload_dir: str = "./uploads"
    log_level: str = "INFO"
    app_name: str = "Semantic Search Engine"
    app_version: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
