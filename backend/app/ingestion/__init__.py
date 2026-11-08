# BrandCanon AI — Ingestion Package
from app.ingestion.file_validator import validate_upload_file, FileValidationResult
from app.ingestion.storage import PrivateStorageService, storage_service
from app.ingestion.text_normalizer import normalize_text
from app.ingestion.chunker import chunk_text, ChunkResult
from app.ingestion.ingestion_service import process_document
from app.ingestion.terminology_engine import TerminologyMatcher, TerminologyMatch

__all__ = [
    "validate_upload_file",
    "FileValidationResult",
    "PrivateStorageService",
    "storage_service",
    "normalize_text",
    "chunk_text",
    "ChunkResult",
    "process_document",
    "TerminologyMatcher",
    "TerminologyMatch",
]
