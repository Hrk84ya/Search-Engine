"""Embedding service using sentence-transformers."""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

_model: Optional[SentenceTransformer] = None
_load_error: Optional[str] = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy-load the embedding model singleton."""
    global _model, _load_error
    if _model is not None:
        return _model
    if _load_error is not None:
        raise RuntimeError(f"Embedding model unavailable: {_load_error}")
    try:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded successfully")
        return _model
    except Exception as e:
        _load_error = str(e)
        logger.error(f"Failed to load embedding model '{settings.embedding_model}': {e}")
        raise RuntimeError(
            f"Embedding model failed to load. Check your network connection or model name "
            f"'{settings.embedding_model}'. Error: {e}"
        ) from e


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return embeddings.tolist()


def generate_single_embedding(text: str) -> List[float]:
    """Generate embedding for a single text."""
    return generate_embeddings([text])[0]
