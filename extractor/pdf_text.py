from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def extract_text(pdf_bytes: bytes) -> str:
    """Pull plain text from a PDF. Empty string if the file has no text layer."""
    reader = PdfReader(BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()
