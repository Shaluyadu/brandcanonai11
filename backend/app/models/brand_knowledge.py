import enum
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid, utc_now


class DocumentProcessingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"
    UNSUPPORTED_SCANNED_DOCUMENT = "UNSUPPORTED_SCANNED_DOCUMENT"


class ApprovalStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"
    EXPIRED = "EXPIRED"


class TerminologyMatchType(str, enum.Enum):
    EXACT = "EXACT"
    WHOLE_WORD = "WHOLE_WORD"
    PHRASE = "PHRASE"


class TerminologySeverity(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BrandProfile(Base, TimestampMixin):
    __tablename__ = "brand_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    brand_name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    domain = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    brand_voice = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    publishing_channels = Column(JSON, default=list, nullable=False)
    applicable_regions = Column(JSON, default=list, nullable=False)

    organisation = relationship("Organisation")


class BrandDocument(Base, TimestampMixin):
    __tablename__ = "brand_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    document_name = Column(String(255), nullable=False)
    storage_key = Column(String(500), nullable=False)  # Private UUID-based storage key
    file_type = Column(String(50), nullable=False)     # 'docx' or 'pdf'
    file_size = Column(Integer, nullable=False)        # In bytes
    current_version = Column(Integer, default=1, nullable=False)
    processing_status = Column(String(50), default=DocumentProcessingStatus.UPLOADED.value, nullable=False, index=True)
    approval_status = Column(String(50), default=ApprovalStatus.PENDING_APPROVAL.value, nullable=False, index=True)

    organisation = relationship("Organisation")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", order_by="DocumentVersion.version_number.desc()")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    facts = relationship("ApprovedFact", back_populates="document")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("brand_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    extraction_status = Column(String(50), default="PENDING", nullable=False)
    extracted_text = Column(Text, nullable=True)                   # Normalized text
    total_pages = Column(Integer, default=1, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    approved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("BrandDocument", back_populates="versions")
    approver = relationship("User", foreign_keys=[approved_by])
    chunks = relationship("DocumentChunk", back_populates="document_version", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("brand_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=True)
    source_location = Column(String(255), nullable=True)
    content_hash = Column(String(64), nullable=False, index=True)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    document = relationship("BrandDocument", back_populates="chunks")
    document_version = relationship("DocumentVersion", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunks_org_doc_ver", "organisation_id", "document_id", "document_version_id"),
    )


class ApprovedFact(Base, TimestampMixin):
    __tablename__ = "approved_facts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_document_id = Column(String(36), ForeignKey("brand_documents.id", ondelete="SET NULL"), nullable=True, index=True)
    document_version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    claim_text = Column(Text, nullable=False)
    category = Column(String(100), default="PRODUCT_SPECIFICATION", nullable=False, index=True)
    evidence_quote = Column(Text, nullable=True)
    source_page = Column(Integer, nullable=True)
    source_location = Column(String(255), nullable=True)
    applicable_region = Column(String(100), default="GLOBAL", nullable=False)
    applicable_audience = Column(String(100), default="ALL", nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default=ApprovalStatus.PENDING_APPROVAL.value, nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    document = relationship("BrandDocument", back_populates="facts")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])


class TerminologyRule(Base, TimestampMixin):
    __tablename__ = "terminology_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    preferred_term = Column(String(255), nullable=False)
    prohibited_term = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    match_type = Column(String(50), default=TerminologyMatchType.EXACT.value, nullable=False)
    case_sensitive = Column(Boolean, default=False, nullable=False)
    category = Column(String(100), default="BRAND_IDENTITY", nullable=False)
    severity = Column(String(50), default=TerminologySeverity.HIGH.value, nullable=False)
    applicable_channel = Column(String(100), default="ALL", nullable=False)
    applicable_region = Column(String(100), default="GLOBAL", nullable=False)
    status = Column(String(50), default=ApprovalStatus.ACTIVE.value if hasattr(ApprovalStatus, 'ACTIVE') else "ACTIVE", nullable=False, index=True)
    source_document_id = Column(String(36), ForeignKey("brand_documents.id", ondelete="SET NULL"), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    source_document = relationship("BrandDocument")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])


class KnowledgeApproval(Base):
    __tablename__ = "knowledge_approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # 'DOCUMENT', 'FACT', 'TERMINOLOGY_RULE'
    entity_id = Column(String(36), nullable=False, index=True)
    decision = Column(String(50), nullable=False)                # 'APPROVED', 'REJECTED', 'ARCHIVED'
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    reviewer = relationship("User")

