"""Semantic search endpoint with RAG."""

import time

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import get_settings
from app.core.logging import logger
from app.models.schemas import SearchRequest, SearchResponse
from app.services.retrieval import search_similar_chunks
from app.services.cache import get_cached_result, set_cached_result
from app.services.tracking import log_search_experiment
from ml.rag.generator import generate_answer

router = APIRouter(tags=["Search"])
settings = get_settings()


@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Perform semantic search with RAG-generated answer."""
    start = time.time()

    # Check cache
    cached = await get_cached_result(request.query, request.top_k)
    if cached:
        return SearchResponse(**cached)

    # Retrieve similar chunks
    chunks = await search_similar_chunks(db, request.query, request.top_k)

    # Generate answer via RAG
    context_texts = [c.chunk_text for c in chunks]
    answer = generate_answer(request.query, context_texts)

    latency_ms = round((time.time() - start) * 1000, 2)

    response = SearchResponse(
        query=request.query,
        retrieved_chunks=[c.model_dump() for c in chunks],
        generated_answer=answer,
        latency_ms=latency_ms,
        model_info={
            "embedding_model": settings.embedding_model,
            "llm_model": settings.llm_model,
            "top_k": request.top_k,
        },
    )

    # Cache result
    await set_cached_result(request.query, request.top_k, response.model_dump())

    # Track in MLflow
    top_sim = chunks[0].similarity_score if chunks else None
    log_search_experiment(
        query=request.query,
        top_k=request.top_k,
        num_results=len(chunks),
        latency_ms=latency_ms,
        embedding_model=settings.embedding_model,
        llm_model=settings.llm_model,
        answer_length=len(answer),
        top_similarity=top_sim,
    )

    logger.info(f"Search completed in {latency_ms}ms — {len(chunks)} results")
    return response
