"""Tests for the text chunking service."""

import pytest
from app.services.chunker import chunk_text


def test_chunk_text_basic():
    text = " ".join(["word"] * 1000)
    chunks = chunk_text(text, chunk_size=400, chunk_overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        words = chunk.split()
        assert len(words) <= 400


def test_chunk_text_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_short():
    text = "This is a short document."
    chunks = chunk_text(text, chunk_size=400, chunk_overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_overlap():
    words = [f"w{i}" for i in range(100)]
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=30, chunk_overlap=10)
    assert len(chunks) > 1
    # Verify overlap exists between consecutive chunks
    first_words = set(chunks[0].split())
    second_words = set(chunks[1].split())
    overlap = first_words & second_words
    assert len(overlap) > 0
