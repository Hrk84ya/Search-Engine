"""MLflow experiment tracking for search and RAG pipeline."""

import time
from typing import List, Optional

import mlflow
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

_initialized = False


def init_mlflow():
    """Initialize MLflow tracking."""
    global _initialized
    if _initialized:
        return
    try:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment("semantic-search-rag")
        _initialized = True
        logger.info(f"MLflow initialized: {settings.mlflow_tracking_uri}")
    except Exception as e:
        logger.warning(f"MLflow unavailable: {e}")


def log_search_experiment(
    query: str,
    top_k: int,
    num_results: int,
    latency_ms: float,
    embedding_model: str,
    llm_model: str,
    answer_length: int,
    top_similarity: Optional[float] = None,
):
    """Log a search query as an MLflow run."""
    try:
        init_mlflow()
        with mlflow.start_run(run_name="search-query", nested=True):
            mlflow.log_params({
                "query": query[:250],
                "top_k": top_k,
                "embedding_model": embedding_model,
                "llm_model": llm_model,
            })
            mlflow.log_metrics({
                "num_results": num_results,
                "latency_ms": latency_ms,
                "answer_length": answer_length,
                "top_similarity_score": top_similarity or 0.0,
            })
    except Exception as e:
        logger.warning(f"MLflow logging failed: {e}")


def log_ingestion_experiment(
    filename: str,
    file_type: str,
    chunk_count: int,
    embedding_model: str,
):
    """Log a document ingestion as an MLflow run."""
    try:
        init_mlflow()
        with mlflow.start_run(run_name="document-ingestion", nested=True):
            mlflow.log_params({
                "filename": filename[:250],
                "file_type": file_type,
                "embedding_model": embedding_model,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
            })
            mlflow.log_metrics({
                "chunk_count": chunk_count,
            })
    except Exception as e:
        logger.warning(f"MLflow logging failed: {e}")
