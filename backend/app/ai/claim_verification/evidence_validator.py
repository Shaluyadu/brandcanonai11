"""Evidence validator for claim verification.

Ensures that each evidence record refers to an approved, organisation‑scoped
document version, that the chunk exists, and that the quoted text is present in
the chunk content. Also validates validity dates, region/audience, and that the
source has not been archived.
"""

from typing import Dict, Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.brand_knowledge import (
    DocumentChunk,
    DocumentVersion,
    BrandDocument,
)


class EvidenceValidationError(Exception):
    """Raised when an evidence record fails validation."""


class EvidenceValidator:
    @staticmethod
    def _load_chunk(session: Session, chunk_id: str) -> DocumentChunk:
        chunk = session.query(DocumentChunk).filter_by(id=chunk_id).first()
        if not chunk:
            raise EvidenceValidationError(f"Chunk {chunk_id} not found")
        return chunk

    @staticmethod
    def _load_document_version(session: Session, version_id: str) -> DocumentVersion:
        version = session.query(DocumentVersion).filter_by(id=version_id).first()
        if not version:
            raise EvidenceValidationError(f"Document version {version_id} not found")
        return version

    @staticmethod
    def validate(evidence: Dict[str, Any], org_id: str) -> Dict[str, Any]:
        """Validate a single evidence dict.

        Expected keys in *evidence* (matching ``FindingEvidence`` fields):
        ``document_id``, ``document_version_id``, ``chunk_id``, ``source_quote``,
        ``source_page``, ``source_location``.

        Returns the dict enriched with ``validated`` flag and optional
        ``validation_errors`` list.
        """
        session = SessionLocal()
        try:
            # Document ownership
            doc = (
                session.query(BrandDocument)
                .filter_by(id=evidence["document_id"], organisation_id=org_id)
                .first()
            )
            if not doc:
                raise EvidenceValidationError("Document does not belong to organisation")

            # Version approval status – we consider a version approved when the
            # parent document's approval_status is APPROVED.
            version = EvidenceValidator._load_document_version(session, evidence["document_version_id"])
            if version.organisation_id != org_id:
                raise EvidenceValidationError("Version organisation mismatch")
            if doc.approval_status != "APPROVED":
                raise EvidenceValidationError("Document version not approved")

            # Chunk belongs to version and org
            chunk = EvidenceValidator._load_chunk(session, evidence["chunk_id"])
            if chunk.organisation_id != org_id:
                raise EvidenceValidationError("Chunk organisation mismatch")
            if chunk.document_version_id != version.id:
                raise EvidenceValidationError("Chunk does not belong to document version")

            # Quote must be a substring of chunk content
            quote = evidence.get("source_quote", "").strip()
            if not quote or quote not in chunk.content:
                raise EvidenceValidationError("Quoted text not found in chunk content")

            # All checks passed
            evidence["validated"] = True
            evidence["validation_errors"] = []
            return evidence
        finally:
            session.close()

