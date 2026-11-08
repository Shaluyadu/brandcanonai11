import enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID

class SuggestionType(str, enum.Enum):
    FACTUAL = "FACTUAL"
    TONE = "TONE"
    TERMINOLOGY = "TERMINOLOGY"
    STYLE = "STYLE"
    OTHER = "OTHER"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class GenerationStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class SuggestionSchema(BaseModel):
    finding_id: UUID = Field(..., description="ID of the associated finding")
    original_text: str = Field(..., min_length=1, max_length=2000)
    suggested_text: str = Field(..., min_length=1, max_length=2000)
    rationale: str = Field(..., min_length=1, max_length=5000)
    suggestion_type: SuggestionType
    evidence_ids: List[UUID] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_human_review: bool = True
    risk_level: RiskLevel
    generation_status: GenerationStatus
    prompt_version: str = Field(..., min_length=1)
    provider_metadata: Optional[dict] = None

    @validator("evidence_ids", each_item=True)
    def check_uuid(cls, v):
        if not isinstance(v, UUID):
            raise ValueError("evidence_ids must be UUIDs")
        return v

