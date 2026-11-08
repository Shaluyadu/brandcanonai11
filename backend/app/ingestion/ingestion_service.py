"""
Synchronous document ingestion orchestration service.

Flow:
  retrieve from storage → parse (DOCX/PDF) → normalize → chunk
  → persist chunks → update DocumentVersion extraction status

Designed to be called inline from API endpoints (Phase 2).
Compatible with async task queues in Phase 3 — just wrap this function.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.brand_knowledge import (
    BrandDocument,
    DocumentVersion,
    DocumentChunk,
    DocumentProcessingStatus,
)
from app.ingestion.storage import PrivateStorageService, storage_service
from app.ingestion.file_validator import FileValidationResult
from app.ingestion.text_normalizer import normalize_text
from app.ingestion.chunker import chunk_text, ChunkResult
from app.ingestion.pdf_parser import parse_pdf, ScannedDocumentError
from app.ingestion.docx_parser import parse_docx
from app.core.exceptions import ValidationError
from app.models.base import generate_uuid, utc_now


def _docx_blocks_to_dicts(blocks) -> list:
    return [
        {
            "text": b.text,
            "page": b.page_number,
            "location": b.location,
        }
        for b in blocks
    ]


def _pdf_pages_to_dicts(pages) -> list:
    result = []
    for page in pages:
        # Split each page by paragraphs to get finer-grained blocks
        paragraphs = [p.strip() for p in page.text.split("\n\n") if p.strip()]
        for para in paragraphs:
            result.append({
                "text": para,
                "page": page.page_number,
                "location": f"Page {page.page_number}",
            })
    return result


def process_document(
    document_id: str,
    organisation_id: str,
    db: Session,
    storage: Optional[PrivateStorageService] = None,
) -> DocumentVersion:
    """
    Load, parse, normalise, and chunk a BrandDocument's latest version.
    Updates DocumentVersion.extraction_status and creates DocumentChunk rows.

    Returns the updated DocumentVersion.
    Raises ValidationError for recoverable parse errors (status → FAILED).
    """
    if storage is None:
        storage = storage_service

    # --- Fetch document record and verify org ownership ---
    doc: Optional[BrandDocument] = db.query(BrandDocument).filter(
        BrandDocument.id == document_id,
        BrandDocument.organisation_id == organisation_id,
    ).first()

    if not doc:
        raise ValidationError(f"Document '{document_id}' not found in organisation")

    # --- Fetch the latest document version ---
    doc_version: Optional[DocumentVersion] = (
        db.query(DocumentVersion)
        .filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == doc.current_version,
        )
        .first()
    )

    if not doc_version:
        raise ValidationError("Document version record not found")

    # Mark as processing
    doc_version.extraction_status = "PROCESSING"
    doc.processing_status = DocumentProcessingStatus.PROCESSING.value
    db.flush()

    try:
        # --- Retrieve raw file bytes ---
        file_content = storage.get_file(organisation_id, doc.storage_key)

        # --- Parse based on file type ---
        raw_text = ""
        total_pages = 1
        blocks = []

        if doc.file_type == "pdf":
            try:
                pages, total_pages = parse_pdf(file_content)
                # Normalize per page then collect blocks
                normalized_pages = []
                for p in pages:
                    norm = normalize_text(p.text)
                    p.text = norm
                    normalized_pages.append(p)
                raw_text = "\n\n".join(p.text for p in normalized_pages if p.text)
                blocks = _pdf_pages_to_dicts(normalized_pages)
            except ScannedDocumentError as exc:
                doc_version.extraction_status = "UNSUPPORTED_SCANNED_DOCUMENT"
                doc.processing_status = DocumentProcessingStatus.UNSUPPORTED_SCANNED_DOCUMENT.value
                db.flush()
                return doc_version

        elif doc.file_type == "docx":
            parsed_blocks = parse_docx(file_content)
            # Normalize each block
            for b in parsed_blocks:
                b.text = normalize_text(b.text)
            raw_text = "\n\n".join(b.text for b in parsed_blocks if b.text)
            blocks = _docx_blocks_to_dicts(parsed_blocks)
            total_pages = 1

        else:
            doc_version.extraction_status = "UNSUPPORTED_FORMAT"
            doc.processing_status = DocumentProcessingStatus.FAILED.value
            db.flush()
            return doc_version

        # Require at least some content
        if not raw_text.strip():
            doc_version.extraction_status = "EMPTY_DOCUMENT"
            doc.processing_status = DocumentProcessingStatus.FAILED.value
            db.flush()
            return doc_version

        # --- Chunk ---
        chunk_results: list[ChunkResult] = chunk_text(blocks, chunk_size=800, overlap=100)

        # --- Delete previous chunks for this version (safe re-process) ---
        db.query(DocumentChunk).filter(
            DocumentChunk.document_version_id == doc_version.id
        ).delete(synchronize_session=False)

        # --- Persist chunks ---
        for chunk in chunk_results:
            db_chunk = DocumentChunk(
                id=generate_uuid(),
                organisation_id=organisation_id,
                document_id=document_id,
                document_version_id=doc_version.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                source_page=chunk.source_page,
                source_location=chunk.source_location,
                content_hash=chunk.content_hash,
                metadata_json=chunk.metadata,
            )
            db.add(db_chunk)

        # --- Update version record ---
        doc_version.extracted_text = raw_text[:500_000]  # Cap at 500K chars
        doc_version.total_pages = total_pages
        doc_version.total_chunks = len(chunk_results)
        doc_version.extraction_status = "EXTRACTED"

        # --- Update document status ---
        doc.processing_status = DocumentProcessingStatus.EXTRACTED.value

        db.flush()
        return doc_version

    except ValidationError:
        db_version = db.query(DocumentVersion).filter(DocumentVersion.id == doc_version.id).first()
        if db_version:
            db_version.extraction_status = "FAILED"
        doc_obj = db.query(BrandDocument).filter(BrandDocument.id == document_id).first()
        if doc_obj:
            doc_obj.processing_status = DocumentProcessingStatus.FAILED.value
        db.flush()
        raise

    except Exception as exc:
        db_version = db.query(DocumentVersion).filter(DocumentVersion.id == doc_version.id).first()
        if db_version:
            db_version.extraction_status = "FAILED"
        doc_obj = db.query(BrandDocument).filter(BrandDocument.id == document_id).first()
        if doc_obj:
            doc_obj.processing_status = DocumentProcessingStatus.FAILED.value
        db.flush()
        raise ValidationError(f"Document processing failed: {str(exc)}")

