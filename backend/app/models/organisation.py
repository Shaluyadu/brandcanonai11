from sqlalchemy import Column, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Organisation(Base, TimestampMixin):
    __tablename__ = "organisations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    industry = Column(String(100), nullable=True)
    domain = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    settings = relationship("OrganisationSettings", back_populates="organisation", uselist=False, cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="organisation", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organisation", cascade="all, delete-orphan")


class OrganisationSettings(Base, TimestampMixin):
    __tablename__ = "organisation_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), unique=True, nullable=False)
    enforce_brand_voice = Column(Boolean, default=True, nullable=False)
    strict_mode = Column(Boolean, default=False, nullable=False)
    custom_metadata = Column(JSON, default=dict, nullable=False)

    organisation = relationship("Organisation", back_populates="settings")

