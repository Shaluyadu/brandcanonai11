from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.user import RoleEnum
from app.schemas.common import EMAIL_REGEX


class MemberInvite(BaseModel):
    email: str = Field(..., pattern=EMAIL_REGEX, min_length=5, max_length=255)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: RoleEnum = Field(default=RoleEnum.CREATOR)
    initial_password: Optional[str] = Field(None, min_length=8)


class MemberRoleUpdate(BaseModel):
    role: RoleEnum


class MemberOut(BaseModel):
    id: str  # Membership ID
    user_id: str
    email: str
    full_name: str
    role: str
    is_default: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
