from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf": "pdf", ".txt": "txt", ".md": "markdown", ".markdown": "markdown"}


class InvalidDocument(ValueError):
    pass


def validate_document(filename: str, data: bytes) -> tuple[str, str]:
    safe_name = Path(filename).name.strip()
    if not safe_name or safe_name in {".", ".."}:
        raise InvalidDocument("A valid filename is required")
    suffix = Path(safe_name).suffix.lower()
    file_type = SUPPORTED_EXTENSIONS.get(suffix)
    if file_type is None:
        raise InvalidDocument("Supported file types are PDF, TXT, and Markdown")
    if not data:
        raise InvalidDocument("The uploaded file is empty")
    if file_type == "pdf":
        if not data.startswith(b"%PDF-"):
            raise InvalidDocument("The file content is not a valid PDF")
    else:
        if b"\x00" in data:
            raise InvalidDocument("Text documents cannot contain binary data")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InvalidDocument("Text documents must use UTF-8 encoding") from exc
    return safe_name[:255], file_type
