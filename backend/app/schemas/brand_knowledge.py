"""
Phase 2 — Brand Knowledge Hub Pydantic schemas.
Follows existing APIResponse<T> envelope convention.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Brand Profile
# ---------------------------------------------------------------------------

class BrandProfileCreate(BaseModel):
    brand_name: str = Field(..., min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    domain: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    publishing_channels: List[str] = Field(default_factory=list)
    applicable_regions: List[str] = Field(default_factory=list)


class BrandProfileUpdate(BaseModel):
    brand_name: Optional[str] = Field(None, min_length=1, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    domain: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    publishing_channels: Optional[List[str]] = None
    applicable_regions: Optional[List[str]] = None


class BrandProfileOut(BaseModel):
    id: str
    organisation_id: str
    brand_name: str
    industry: Optional[str]
    domain: Optional[str]
    description: Optional[str]
    brand_voice: Optional[str]
    target_audience: Optional[str]
    publishing_channels: List[str]
    applicable_regions: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

class DocumentVersionOut(BaseModel):
    id: str
    version_number: int
    content_hash: str
    extraction_status: str
    total_pages: int
    total_chunks: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: str
    organisation_id: str
    document_name: str
    file_type: str
    file_size: int
    current_version: int
    processing_status: str
    approval_status: str
    uploaded_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetailOut(DocumentOut):
    versions: List[DocumentVersionOut] = []


class ChunkOut(BaseModel):
    id: str
    chunk_index: int
    content: str
    source_page: Optional[int]
    source_location: Optional[str]
    content_hash: str

    model_config = {"from_attributes": True}


class DocumentContentOut(BaseModel):
    document_id: str
    document_name: str
    extraction_status: str
    total_pages: int
    total_chunks: int
    text_preview: str  # Truncated extracted text
    chunks: List[ChunkOut] = []


# ---------------------------------------------------------------------------
# Approved Facts
# ---------------------------------------------------------------------------

class ApprovedFactCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    claim_text: str = Field(..., min_length=1)
    category: str = Field(default="PRODUCT_SPECIFICATION", max_length=100)
    evidence_quote: Optional[str] = None
    source_page: Optional[int] = None
    source_location: Optional[str] = Field(None, max_length=255)
    applicable_region: str = Field(default="GLOBAL", max_length=100)
    applicable_audience: str = Field(default="ALL", max_length=100)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    brand_document_id: Optional[str] = None


class ApprovedFactUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    claim_text: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    evidence_quote: Optional[str] = None
    source_page: Optional[int] = None
    source_location: Optional[str] = Field(None, max_length=255)
    applicable_region: Optional[str] = Field(None, max_length=100)
    applicable_audience: Optional[str] = Field(None, max_length=100)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class ApprovedFactOut(BaseModel):
    id: str
    organisation_id: str
    brand_document_id: Optional[str]
    title: str
    claim_text: str
    category: str
    evidence_quote: Optional[str]
    source_page: Optional[int]
    source_location: Optional[str]
    applicable_region: str
    applicable_audience: str
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    status: str
    created_by: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Terminology Rules
# ---------------------------------------------------------------------------

class TerminologyRuleCreate(BaseModel):
    preferred_term: str = Field(..., min_length=1, max_length=255)
    prohibited_term: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    match_type: str = Field(default="EXACT", pattern="^(EXACT|WHOLE_WORD|PHRASE)$")
    case_sensitive: bool = False
    category: str = Field(default="BRAND_IDENTITY", max_length=100)
    severity: str = Field(default="HIGH", pattern="^(HIGH|MEDIUM|LOW)$")
    applicable_channel: str = Field(default="ALL", max_length=100)
    applicable_region: str = Field(default="GLOBAL", max_length=100)
    source_document_id: Optional[str] = None


class TerminologyRuleUpdate(BaseModel):
    preferred_term: Optional[str] = Field(None, min_length=1, max_length=255)
    prohibited_term: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    match_type: Optional[str] = Field(None, pattern="^(EXACT|WHOLE_WORD|PHRASE)$")
    case_sensitive: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=100)
    severity: Optional[str] = Field(None, pattern="^(HIGH|MEDIUM|LOW)$")
    applicable_channel: Optional[str] = Field(None, max_length=100)
    applicable_region: Optional[str] = Field(None, max_length=100)


class TerminologyRuleOut(BaseModel):
    id: str
    organisation_id: str
    preferred_term: str
    prohibited_term: str
    description: Optional[str]
    match_type: str
    case_sensitive: bool
    category: str
    severity: str
    applicable_channel: str
    applicable_region: str
    status: str
    source_document_id: Optional[str]
    created_by: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Approval decisions
# ---------------------------------------------------------------------------

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED|ARCHIVED)$")
    reason: Optional[str] = Field(None, max_length=2000)


# ---------------------------------------------------------------------------
# Knowledge Approval records
# ---------------------------------------------------------------------------

class KnowledgeApprovalOut(BaseModel):
    id: str
    organisation_id: str
    entity_type: str
    entity_id: str
    decision: str
    reviewer_id: str
    reason: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Overview / Dashboard stats
# ---------------------------------------------------------------------------

class KnowledgeOverviewStats(BaseModel):
    total_documents: int
    approved_documents: int
    pending_documents: int
    total_facts: int
    approved_facts: int
    pending_facts: int
    total_terminology_rules: int
    active_terminology_rules: int
    pending_terminology_rules: int
    total_chunks: int

