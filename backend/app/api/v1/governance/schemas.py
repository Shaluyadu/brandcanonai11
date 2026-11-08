from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.common import APIResponse, PaginatedResponse, PaginationParams

class DashboardStats(BaseModel):
    total_submissions: int = Field(..., description="Total number of content submissions in the organisation")
    pending_reviews: int = Field(..., description="Submissions with a ReviewResult that is not yet completed")
    in_review: int = Field(..., description="Submissions whose ReviewResult is currently queued or preparing")
    changes_requested: int = Field(..., description="Findings with status REJECTED indicating changes required")
    approved: int = Field(..., description="Submissions with ReviewResult overall_status == COMPLETED and no blocking findings")
    rejected: int = Field(..., description="Submissions whose ReviewResult overall_status == FAILED or CANCELLED")
    review_incomplete: int = Field(..., description="Submissions where ReviewResult overall_status == INCOMPLETE")
    high_risk_findings: int = Field(..., description="Count of findings with severity CRITICAL or HIGH")

class SubmissionListItem(BaseModel):
    id: str
    title: str
    content_type: str = "ARTICLE"
    current_status: str
    publishing_channel: str
    campaign_name: Optional[str] = None
    target_audience: Optional[str] = None
    intended_publication_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    latest_review_status: Optional[str] = None

class SubmissionsResponse(PaginatedResponse[SubmissionListItem]):
    pass

class SubmissionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field("ARTICLE", max_length=100)
    publishing_channel: str = Field("WEB", max_length=100)
    campaign_name: Optional[str] = Field(None, max_length=255)
    target_audience: Optional[str] = Field(None, max_length=255)
    applicable_region: str = Field("GLOBAL", max_length=100)
    language: str = Field("en", max_length=50)
    description: Optional[str] = None
    content_text: str = Field(..., min_length=1)

class ContentVersionDetail(BaseModel):
    id: str
    version_number: int
    content_text: str
    content_hash: str
    word_count: int
    character_count: int
    created_at: datetime

class SuggestionDetail(BaseModel):
    id: str
    finding_id: str
    original_text: str
    suggested_text: str
    reason: str
    status: str
    created_at: datetime

class EvidenceDetail(BaseModel):
    id: str
    finding_id: str
    document_id: str
    document_version_id: str
    chunk_id: str
    source_quote: str
    source_page: Optional[int] = None
    source_location: Optional[str] = None
    relevance_metadata: Dict[str, Any] = Field(default_factory=dict)
    verification_status: str
    created_at: datetime

class FindingDetail(BaseModel):
    id: str
    category: str
    status: str
    severity: str
    confidence_level: str
    original_text: str
    start_offset: int
    end_offset: int
    explanation: Optional[str] = None
    suggestion: Optional[SuggestionDetail] = None
    evidences: List[EvidenceDetail] = Field(default_factory=list)
    created_at: datetime

class ReviewResultDetail(BaseModel):
    id: str
    overall_status: str
    findings_count: int
    model_provider: Optional[str] = None
    model_identifier: Optional[str] = None
    findings: List[FindingDetail] = Field(default_factory=list)
    created_at: datetime

class SubmissionDetail(BaseModel):
    id: str
    organisation_id: str
    creator_id: Optional[str] = None
    title: str
    content_type: str
    publishing_channel: str
    campaign_name: Optional[str] = None
    target_audience: Optional[str] = None
    applicable_region: str
    language: str
    description: Optional[str] = None
    current_status: str
    current_version_number: int
    created_at: datetime
    updated_at: datetime
    versions: List[ContentVersionDetail] = Field(default_factory=list)
    latest_review_result: Optional[ReviewResultDetail] = None

class ReviewDecisionCreate(BaseModel):
    decision: str = Field(..., description="APPROVED, REQUEST_CHANGES, or REJECTED")
    notes: Optional[str] = Field(None, description="Reviewer feedback or rationale")

class SuggestionAction(BaseModel):
    action: str = Field(..., description="APPLY or REJECT")

class EvidenceResponse(APIResponse[EvidenceDetail]):
    pass

class SubmissionDetailResponse(APIResponse[SubmissionDetail]):
    pass
