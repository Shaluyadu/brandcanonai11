"""
BrandCanon AI — Phase 3: Content Submissions, Version Control & Review Queue Models.
"""
import enum
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid, utc_now


class SubmissionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    QUEUED_FOR_REVIEW = "QUEUED_FOR_REVIEW"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class ReviewJobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ContentSubmission(Base, TimestampMixin):
    __tablename__ = "content_submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False, index=True)
    publishing_channel = Column(String(100), nullable=False, index=True)
    campaign_name = Column(String(255), nullable=True, index=True)
    target_audience = Column(String(255), nullable=True)
    applicable_region = Column(String(100), default="GLOBAL", nullable=False)
    language = Column(String(50), default="en", nullable=False)
    description = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    intended_publication_date = Column(DateTime(timezone=True), nullable=True)
    current_status = Column(String(50), default=SubmissionStatus.DRAFT.value, nullable=False, index=True)
    current_version_number = Column(Integer, default=1, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    organisation = relationship("Organisation")
    creator = relationship("User", foreign_keys=[creator_id])
    versions = relationship(
        "ContentVersion",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="ContentVersion.version_number.desc()"
    )
    review_jobs = relationship(
        "ReviewJob",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="ReviewJob.created_at.desc()"
    )

    __table_args__ = (
        Index("ix_submissions_org_status", "organisation_id", "current_status"),
        Index("ix_submissions_org_creator", "organisation_id", "creator_id"),
    )


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    content_text = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    source_file_id = Column(String(500), nullable=True)           # Storage key if uploaded from DOCX
    source_file_name = Column(String(255), nullable=True)
    change_note = Column(String(500), nullable=True)
    word_count = Column(Integer, default=0, nullable=False)
    character_count = Column(Integer, default=0, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    submission = relationship("ContentSubmission", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])
    review_jobs = relationship("ReviewJob", back_populates="content_version")

    __table_args__ = (
        UniqueConstraint("submission_id", "version_number", name="uq_submission_version"),
        Index("ix_content_versions_org_sub", "organisation_id", "submission_id"),
    )


class ReviewJob(Base, TimestampMixin):
    __tablename__ = "review_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    content_version_id = Column(String(36), ForeignKey("content_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    job_status = Column(String(50), default=ReviewJobStatus.QUEUED.value, nullable=False, index=True)
    error_code = Column(String(100), nullable=True)
    error_message_safe = Column(Text, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    preflight_checks = Column(JSON, default=dict, nullable=False)
    queued_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    submission = relationship("ContentSubmission", back_populates="review_jobs")
    content_version = relationship("ContentVersion", back_populates="review_jobs")
    requester = relationship("User", foreign_keys=[requested_by])

    __table_args__ = (
        Index("ix_review_jobs_org_status", "organisation_id", "job_status"),
        Index("ix_review_jobs_sub_ver", "submission_id", "content_version_id"),
    )
