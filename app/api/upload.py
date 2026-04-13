"""Document upload and management endpoints."""

import os
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.db.session import get_db
from app.core.config import get_settings
from app.core.logging import logger
from app.core.auth import require_auth
from app.core.rate_limit import rate_limit
from app.models.schemas import UploadResponse, DeleteResponse, DocumentResponse
from app.models.document import Document, DocumentChunk
from app.services.ingestion import ingest_document
from app.services.tracking import log_ingestion_experiment

router = APIRouter(tags=["Documents"])
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=UploadResponse, dependencies=[Depends(rate_limit(max_requests=5, window_seconds=60))])
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_auth),
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
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB.",
            )
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


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_auth),
):
    """List all indexed documents, newest first."""
    result = await db.execute(
        select(Document)
        .order_by(Document.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(require_auth),
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
