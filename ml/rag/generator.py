"""RAG text generation using Hugging Face transformers."""

from typing import List, Optional
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()

_tokenizer = None
_model = None
_load_error: Optional[str] = None


def _load_model():
    """Lazy-load the LLM model and tokenizer."""
    global _tokenizer, _model, _load_error
    if _model is not None:
        return _tokenizer, _model
    if _load_error is not None:
        raise RuntimeError(f"LLM unavailable: {_load_error}")
    try:
        logger.info(f"Loading LLM: {settings.llm_model}")
        _tokenizer = AutoTokenizer.from_pretrained(settings.llm_model)
        _model = AutoModelForSeq2SeqLM.from_pretrained(settings.llm_model)
        logger.info("LLM loaded successfully")
        return _tokenizer, _model
    except Exception as e:
        _load_error = str(e)
        logger.error(f"Failed to load LLM '{settings.llm_model}': {e}")
        raise RuntimeError(
            f"LLM failed to load. Check your network connection or model name "
            f"'{settings.llm_model}'. Error: {e}"
        ) from e
    return _tokenizer, _model


def build_rag_prompt(query: str, context_chunks: List[str]) -> str:
    """Build a grounded prompt from retrieved chunks.

    Uses a single-line format that flan-t5 handles well.
    """
    # Limit context to stay within model's effective range
    max_context_chars = 1200
    context_parts = []
    total = 0
    for chunk in context_chunks:
        if total + len(chunk) > max_context_chars:
            trimmed = chunk[:max_context_chars - total]
            if trimmed.strip():
                context_parts.append(trimmed.strip())
            break
        context_parts.append(chunk)
        total += len(chunk)

    context = " ".join(context_parts)
    prompt = f"Answer the question using the context. Context: {context} Question: {query}"
    return prompt


def generate_answer(query: str, context_chunks: List[str]) -> str:
    """Generate a grounded answer using RAG.

    Uses direct model.generate() to avoid pipeline API inconsistencies
    across transformers versions.
    """
    if not context_chunks:
        return "No relevant documents found to answer this question."

    tokenizer, model = _load_model()
    prompt = build_rag_prompt(query, context_chunks)

    inputs = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=False,
        num_beams=2,
        early_stopping=True,
    )
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    if not answer:
        return "The model could not generate an answer from the provided context."

    return answer
