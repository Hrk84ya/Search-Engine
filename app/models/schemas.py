"""Pydantic schemas for API request/response models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ChunkResult(BaseModel):
    chunk_id: UUID
    document_id: UUID
    chunk_text: str
    similarity_score: float
    chunk_index: int


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResponse(BaseModel):
    query: str
    retrieved_chunks: List[ChunkResult]
    generated_answer: str
    latency_ms: float
    model_info: dict


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UploadResponse(BaseModel):
    document_id: UUID
    filename: str
    chunk_count: int
    message: str
