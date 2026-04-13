"""Tests for document parsing."""

import os
import tempfile
import pytest
from app.services.document_parser import parse_document


def test_parse_txt():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Hello, this is a test document.\nSecond line.")
        f.flush()
        result = parse_document(f.name)
    os.unlink(f.name)
    assert "Hello" in result
    assert "Second line" in result


def test_parse_unsupported():
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        f.write(b"data")
        f.flush()
    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_document(f.name)
    os.unlink(f.name)
