"""Text chunking service with configurable size and overlap."""

from typing import List
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[str]:
    """Split text into overlapping chunks by word count.

    Args:
        text: The full document text.
        chunk_size: Target number of words per chunk (default from settings).
        chunk_overlap: Number of overlapping words between chunks.

    Returns:
        List of text chunks.
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - chunk_overlap

    logger.info(f"Created {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks
