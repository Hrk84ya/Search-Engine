"""Document parsing for PDF, TXT, and DOCX files."""

import os
from typing import List
from app.core.logging import logger


def parse_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def parse_pdf(file_path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def parse_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


PARSERS = {
    ".txt": parse_txt,
    ".pdf": parse_pdf,
    ".docx": parse_docx,
}


def parse_document(file_path: str) -> str:
    """Parse a document file and return its text content."""
    ext = os.path.splitext(file_path)[1].lower()
    parser = PARSERS.get(ext)
    if parser is None:
        raise ValueError(f"Unsupported file type: {ext}")
    logger.info(f"Parsing {ext} file: {file_path}")
    return parser(file_path)
