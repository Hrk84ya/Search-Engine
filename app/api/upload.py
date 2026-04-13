"""Document upload and management endpoints."""

import os
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.db.session import get_db
from app.core.config import get_settings
from app.core.logging import logger
from app.models.schemas import UploadResponse, DeleteResponse
from app.models.document import Document, DocumentChunk
from app.services.ingestion import ingest_document
from app.services.tracking import log_ingestion_experiment

router = APIRouter(tags=["Documents"])
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload and index a document (PDF, TXT, DOCX)."""
    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Save file to disk
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.upload_dir, f"{file_id}{ext}")

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Ingest: parse → chunk → embed → store
    try:
        doc_id, chunk_count = await ingest_document(
            db=db,
            file_path=file_path,
            filename=file.filename,
            file_type=ext.lstrip("."),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail="Document ingestion failed")
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)

    # Track in MLflow
    log_ingestion_experiment(
        filename=file.filename,
        file_type=ext.lstrip("."),
        chunk_count=chunk_count,
        embedding_model=settings.embedding_model,
    )

    return UploadResponse(
        document_id=doc_id,
        filename=file.filename,
        chunk_count=chunk_count,
        message=f"Document indexed successfully with {chunk_count} chunks.",
    )


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and all its chunks."""
    # Fetch the document
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = doc.filename

    # Delete chunks first, then the document
    await db.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    await db.delete(doc)
    await db.commit()

    logger.info(f"Deleted document {document_id} ({filename})")

    return DeleteResponse(
        document_id=document_id,
        filename=filename,
        message=f"Document '{filename}' and all its chunks deleted successfully.",
    )
