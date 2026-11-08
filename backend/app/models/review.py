import enum
from .content_submission import ReviewJob, ReviewJobStatus
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid, utc_now


class ReviewOverallStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    INCOMPLETE = "INCOMPLETE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ReviewResult(Base, TimestampMixin):
    __tablename__ = "review_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    review_job_id = Column(String(36), ForeignKey("review_jobs.id", ondelete="CASCADE"), nullable=False, unique=True)
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False)
    content_version_id = Column(String(36), ForeignKey("content_versions.id", ondelete="CASCADE"), nullable=False)
    overall_status = Column(String(50), default=ReviewOverallStatus.COMPLETED.value, nullable=False, index=True)
    findings_count = Column(Integer, default=0, nullable=False)
    review_started_at = Column(DateTime(timezone=True), nullable=True)
    review_completed_at = Column(DateTime(timezone=True), nullable=True)
    model_provider = Column(String(100), nullable=True)
    model_identifier = Column(String(100), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    prompt_version = Column(String(50), nullable=True)
    review_configuration = Column(JSON, default=dict, nullable=False)
    knowledge_snapshot_reference = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    review_job = relationship("ReviewJob")
    submission = relationship("ContentSubmission")
    content_version = relationship("ContentVersion")
    findings = relationship(
        "Finding",
        back_populates="review_result",
        cascade="all, delete-orphan",
        order_by="Finding.created_at.desc()",
    )
    component_executions = relationship(
        "ReviewComponentExecution",
        back_populates="review_result",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_review_results_org_status", "organisation_id", "overall_status"),
    )


class FindingCategory(str, enum.Enum):
    TERMINOLOGY = "TERMINOLOGY"
    CLAIM = "CLAIM"
    EVIDENCE = "EVIDENCE"
    SUGGESTION = "SUGGESTION"


class FindingStatus(str, enum.Enum):
    DETECTED = "DETECTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class SeverityLevel(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ConfidenceLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Finding(Base, TimestampMixin):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    review_result_id = Column(String(36), ForeignKey("review_results.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    status = Column(String(50), default=FindingStatus.DETECTED.value, nullable=False)
    severity = Column(String(20), nullable=False)
    confidence_level = Column(String(20), nullable=False)
    original_text = Column(Text, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    verification_metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    review_result = relationship("ReviewResult", back_populates="findings")
    evidences = relationship(
        "FindingEvidence",
        back_populates="finding",
        cascade="all, delete-orphan",
    )
    suggestion = relationship("Suggestion", uselist=False, back_populates="finding")

    __table_args__ = (
        Index("ix_findings_org_category", "organisation_id", "category"),
    )


class FindingEvidence(Base, TimestampMixin):
    __tablename__ = "finding_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(36), nullable=False)
    document_version_id = Column(String(36), nullable=False)
    chunk_id = Column(String(36), nullable=False)
    source_quote = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=True)
    source_location = Column(String(255), nullable=True)
    relevance_metadata = Column(JSON, default=dict, nullable=False)
    verification_status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    finding = relationship("Finding", back_populates="evidences")

    __table_args__ = (
        Index("ix_finding_evidence_org_doc", "organisation_id", "document_id"),
    )


class Suggestion(Base, TimestampMixin):
    __tablename__ = "suggestions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, unique=True)
    original_text = Column(Text, nullable=False)
    suggested_text = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    finding = relationship("Finding", back_populates="suggestion")

    __table_args__ = (
        Index("ix_suggestions_org_finding", "organisation_id", "finding_id"),
    )


class ReviewComponentExecution(Base, TimestampMixin):
    __tablename__ = "review_component_executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    review_result_id = Column(String(36), ForeignKey("review_results.id", ondelete="CASCADE"), nullable=False)
    component_name = Column(String(100), nullable=False)
    execution_status = Column(String(50), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    error_code = Column(String(100), nullable=True)
    execution_metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    review_result = relationship("ReviewResult", back_populates="component_executions")

    __table_args__ = (
        Index("ix_component_exec_org_result", "organisation_id", "review_result_id"),
    )
