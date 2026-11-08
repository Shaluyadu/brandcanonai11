'''Pydantic schemas for claim verification engine.'''

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    NOT_FOUND = "NOT_FOUND"
    OUTDATED = "OUTDATED"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    NOT_CHECKED = "NOT_CHECKED"


class VerificationResultSchema(BaseModel):
    verification_status: VerificationStatus = Field(..., description="Final verification outcome")
    reasoning: str = Field(..., description="Human‑readable explanation from the LLM")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence that support the claim")
    contradicting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence that contradict the claim")
    confidence_level: Optional[str] = Field(
        None, description="LLM confidence (e.g., high/medium/low)"
    )
    requires_human_review: bool = Field(
        False, description="Whether a human should review this verification"
    )


class VerificationEvidenceSchema(BaseModel):
    document_id: str = Field(..., description="UUID of the source document")
    document_version_id: str = Field(..., description="UUID of the approved document version")
    chunk_id: str = Field(..., description="UUID of the document chunk used as evidence")
    source_quote: str = Field(..., description="Exact quoted text from the chunk")
    source_page: Optional[int] = Field(None, description="Page number if available")
    source_location: Optional[str] = Field(
        None, description="Additional location info (e.g., paragraph, section)"
    )
    relevance_score: Optional[float] = Field(
        None, description="Score from the RAG retrieval (0‑1)"
    )

