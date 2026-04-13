"""Vector similarity retrieval service."""

from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, literal_column, cast
from pgvector.sqlalchemy import Vector

from app.core.config import get_settings
from app.core.logging import logger
from app.models.document import DocumentChunk
from app.models.schemas import ChunkResult
from ml.embedding.embedder import generate_single_embedding

settings = get_settings()


async def search_similar_chunks(
    db: AsyncSession,
    query: str,
    top_k: int = None,
) -> List[ChunkResult]:
    """Perform cosine similarity search against stored embeddings.

    Args:
        db: Async database session.
        query: User search query.
        top_k: Number of results to return.

    Returns:
        List of ChunkResult with similarity scores.
    """
    top_k = top_k or settings.top_k

    # Generate query embedding
    query_embedding = generate_single_embedding(query)

    # Cosine similarity search via pgvector SQLAlchemy operators
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)
    similarity = (1 - distance).label("similarity")

    # Fetch more than needed to allow dedup, then trim
    fetch_limit = top_k * 3

    stmt = (
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.chunk_text,
            DocumentChunk.chunk_index,
            similarity,
        )
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(distance)
        .limit(fetch_limit)
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    # Deduplicate by chunk_text — keep highest scoring version
    seen_texts = set()
    chunks = []
    for row in rows:
        text_key = row.chunk_text.strip()[:200]  # compare first 200 chars
        if text_key in seen_texts:
            continue
        seen_texts.add(text_key)
        chunks.append(
            ChunkResult(
                chunk_id=row.id,
                document_id=row.document_id,
                chunk_text=row.chunk_text,
                similarity_score=round(float(row.similarity), 4),
                chunk_index=row.chunk_index,
            )
        )
        if len(chunks) >= top_k:
            break

    logger.info(f"Retrieved {len(chunks)} chunks for query: '{query[:50]}...'")
    return chunks
