"""Extract plain text from an uploaded CV / transcript file.

Supports PDF, DOCX, and plain text. Image-only (scanned) PDFs yield no text —
the caller should surface that to the user.
"""
from __future__ import annotations

from io import BytesIO

SUPPORTED = (".pdf", ".docx", ".txt", ".md")


def extract_text(filename: str, data: bytes) -> str:
    """Return the text content of an uploaded file, chosen by extension."""
    name = (filename or "").lower()

    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        pages = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(pages).strip()

    if name.endswith(".docx"):
        import docx

        doc = docx.Document(BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs).strip()

    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="replace").strip()

    raise ValueError(
        f"Unsupported file type for {filename!r}. Use one of: {', '.join(SUPPORTED)}."
    )
