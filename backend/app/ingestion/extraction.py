from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedPage:
    content: str
    page_number: int | None


def extract_document(data: bytes, file_type: str) -> list[ExtractedPage]:
    if file_type == "pdf":
        reader = PdfReader(BytesIO(data), strict=True)
        pages = [
            ExtractedPage(content=(page.extract_text() or "").strip(), page_number=index)
            for index, page in enumerate(reader.pages, start=1)
        ]
        if not any(page.content for page in pages):
            raise ValueError("The PDF contains no extractable text")
        return [page for page in pages if page.content]
    if file_type in {"txt", "markdown"}:
        content = data.decode("utf-8").strip()
        if not content:
            raise ValueError("The document contains no text")
        return [ExtractedPage(content=content, page_number=None)]
    raise ValueError(f"Unsupported document type: {file_type}")
