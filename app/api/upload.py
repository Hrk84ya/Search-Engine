"""Document upload endpoint."""

import os
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import get_settings
from app.core.logging import logger
from app.models.schemas import UploadResponse
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
