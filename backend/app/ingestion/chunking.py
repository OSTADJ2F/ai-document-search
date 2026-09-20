import re
from dataclasses import dataclass

from app.ingestion.extraction import ExtractedPage


@dataclass(frozen=True)
class TextChunk:
    content: str
    page_number: int | None
    section: str | None
    token_count: int


def chunk_pages(
    pages: list[ExtractedPage], chunk_size: int = 700, overlap: int = 100
) -> list[TextChunk]:
    if chunk_size <= overlap:
        raise ValueError("Chunk size must be larger than overlap")
    chunks: list[TextChunk] = []
    for page in pages:
        words = page.content.split()
        position = 0
        while position < len(words):
            end = min(position + chunk_size, len(words))
            content = " ".join(words[position:end]).strip()
            heading = _nearest_heading(page.content, content) if page.page_number is None else None
            if content:
                chunks.append(
                    TextChunk(
                        content=content,
                        page_number=page.page_number,
                        section=heading,
                        token_count=len(words[position:end]),
                    )
                )
            if end == len(words):
                break
            position = end - overlap
    return chunks


def _nearest_heading(full_text: str, chunk_text: str) -> str | None:
    chunk_start = full_text.find(chunk_text[: min(80, len(chunk_text))])
    prefix = full_text[: max(0, chunk_start) + min(500, len(chunk_text))]
    headings = re.findall(r"^#{1,6}\s+(.+)$", prefix, flags=re.MULTILINE)
    return headings[-1].strip()[:500] if headings else None
