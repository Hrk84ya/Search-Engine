"""Document ingestion service — parse, chunk, embed, store."""

import os
import uuid
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import logger
from app.models.document import Document, DocumentChunk
from app.services.document_parser import parse_document
from app.services.chunker import chunk_text
from ml.embedding.embedder import generate_embeddings

settings = get_settings()


async def ingest_document(
    db: AsyncSession,
    file_path: str,
    filename: str,
    file_type: str,
) -> Tuple[uuid.UUID, int]:
    """Full ingestion pipeline: parse → chunk → embed → store.

    Returns:
        Tuple of (document_id, chunk_count).
    """
    # 1. Parse
    logger.info(f"Ingesting document: {filename}")
    content = parse_document(file_path)

    # 2. Create document record
    doc = Document(
        filename=filename,
        file_type=file_type,
        content=content[:5000],  # store preview only
    )
    db.add(doc)
    await db.flush()

    # 3. Chunk
    chunks = chunk_text(content)
    if not chunks:
        logger.warning(f"No chunks generated for {filename}")
        doc.chunk_count = 0
        return doc.id, 0

    # 4. Generate embeddings in batch
    logger.info(f"Generating embeddings for {len(chunks)} chunks")
    embeddings = generate_embeddings(chunks)

    # 5. Store chunks with embeddings
    chunk_records = []
    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        chunk_records.append(
            DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                chunk_text=chunk,
                embedding=emb,
            )
        )
    db.add_all(chunk_records)

    doc.chunk_count = len(chunks)
    logger.info(f"Ingested {filename}: {len(chunks)} chunks stored")

    return doc.id, len(chunks)
