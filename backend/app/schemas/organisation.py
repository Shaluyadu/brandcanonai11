from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class OrganisationSettingsBase(BaseModel):
    enforce_brand_voice: bool = True
    strict_mode: bool = False
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)


class OrganisationSettingsUpdate(BaseModel):
    enforce_brand_voice: Optional[bool] = None
    strict_mode: Optional[bool] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class OrganisationSettingsOut(OrganisationSettingsBase):
    id: str
    organisation_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganisationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    domain: Optional[str] = Field(None, max_length=255)


class OrganisationCreate(OrganisationBase):
    pass


class OrganisationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    domain: Optional[str] = Field(None, max_length=255)


class OrganisationOut(OrganisationBase):
    id: str
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganisationDetailOut(OrganisationOut):
    settings: Optional[OrganisationSettingsOut] = None

    model_config = ConfigDict(from_attributes=True)
