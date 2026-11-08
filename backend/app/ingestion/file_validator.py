import os
import re
import hashlib
import zipfile
import io
from typing import Tuple
from app.core.exceptions import ValidationError

# Allowed extensions and standard MIME types
ALLOWED_EXTENSIONS = {".docx", ".pdf"}
ALLOWED_MIMETYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/x-pdf",
    "application/octet-stream", # Often sent by generic form clients, verified via magic bytes
}

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


class FileValidationResult:
    def __init__(self, is_valid: bool, file_type: str, content_hash: str, error: str = None, sanitized_name: str = "", file_size: int = 0):
        self.is_valid = is_valid
        self.file_type = file_type  # 'docx' or 'pdf'
        self.content_hash = content_hash
        self.error = error
        self.sanitized_name = sanitized_name
        self.file_size = file_size


def sanitize_filename(filename: str) -> str:
    """Sanitize user-provided filename to prevent path traversal and shell injection."""
    base = os.path.basename(filename)
    clean = re.sub(r"[^\w\s.-]", "", base).strip()
    return clean or "document"


def validate_document_file(filename: str, content: bytes, content_type: str = "") -> FileValidationResult:
    """
    Validate uploaded document against extension, size, magic numbers, and structure.
    Does NOT trust browser MIME type or file extension alone.
    """
    sanitized = sanitize_filename(filename)
    file_size = len(content) if content else 0

    if not content or file_size == 0:
        return FileValidationResult(False, "", "", "Uploaded file is empty (0 bytes)", sanitized, file_size)

    if file_size > MAX_FILE_SIZE:
        return FileValidationResult(False, "", "", f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB", sanitized, file_size)

    # Extension check
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        return FileValidationResult(
            False, "", "",
            f"Unsupported file format '{ext}'. BrandCanon AI supports .docx and text-based .pdf",
            sanitized, file_size
        )

    content_hash = hashlib.sha256(content).hexdigest()

    # Magic byte and structural inspection
    if ext == ".pdf":
        if not content.startswith(b"%PDF-"):
            return FileValidationResult(False, "", "", "Invalid PDF file: Missing %PDF- magic signature header", sanitized, file_size)
        return FileValidationResult(True, "pdf", content_hash, sanitized_name=sanitized, file_size=file_size)

    elif ext == ".docx":
        # DOCX is an OPC Zip archive containing 'word/document.xml'
        if not content.startswith(b"PK\x03\x04"):
            return FileValidationResult(False, "", "", "Invalid DOCX file: Missing PK ZIP magic signature header", sanitized, file_size)
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                namelist = zf.namelist()
                if "word/document.xml" not in namelist:
                    return FileValidationResult(
                        False, "", "", "Invalid DOCX structure: Missing required 'word/document.xml' container",
                        sanitized, file_size
                    )
        except zipfile.BadZipFile:
            return FileValidationResult(False, "", "", "Corrupted or malformed DOCX archive", sanitized, file_size)

        return FileValidationResult(True, "docx", content_hash, sanitized_name=sanitized, file_size=file_size)

    return FileValidationResult(False, "", "", "Unsupported file type", sanitized, file_size)


def validate_upload_file(content: bytes, filename: str) -> FileValidationResult:
    """Convenience helper for API upload endpoints that raises ValidationError on invalid file."""
    res = validate_document_file(filename=filename, content=content)
    if not res.is_valid:
        raise ValidationError(res.error)
    return res


