"""Document parsing + chunking for company uploads and regulation texts."""

from pathlib import Path


def parse_file(path: Path) -> str:
    """Extract plain text from a PDF/DOCX/TXT upload."""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        import fitz  # pymupdf

        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc)

    if suffix == ".docx":
        import docx

        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)

    return path.read_text(encoding="utf-8")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Simple sliding-window chunker on whitespace-split tokens.

    Good enough for a first pass; swap for a legal-text-aware splitter (e.g. splitting on
    article/recital boundaries for regulation texts) once the pipeline is working end to end.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
    return chunks
