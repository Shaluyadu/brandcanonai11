from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.schemas.common import EMAIL_REGEX
from app.schemas.organisation import OrganisationOut


class UserBase(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, min_length=5, max_length=255)
    full_name: str = Field(..., min_length=2, max_length=255)


class UserRegister(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    organisation_name: Optional[str] = Field(None, min_length=2, max_length=255)


class UserLogin(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, min_length=5, max_length=255)
    password: str = Field(..., min_length=1)


class UserOut(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MembershipOut(BaseModel):
    id: str
    organisation_id: str
    user_id: str
    role: str
    is_default: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    active_organisation: OrganisationOut
    current_role: str


class MeResponse(BaseModel):
    user: UserOut
    active_organisation: OrganisationOut
    current_role: str
    permitted_organisations: List[OrganisationOut]
