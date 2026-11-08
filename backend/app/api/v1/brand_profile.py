"""
Brand Profile API endpoints.
Manage basic brand voice, identity, and target audience settings for an organisation.
"""
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundError, ConflictError
from app.api.deps import (
    get_current_user,
    get_current_tenant,
    require_role,
    record_audit_log
)
from app.models.user import User, Membership, RoleEnum
from app.models.organisation import Organisation
from app.models.brand_knowledge import BrandProfile
from app.schemas.common import APIResponse
from app.schemas.brand_knowledge import (
    BrandProfileCreate,
    BrandProfileUpdate,
    BrandProfileOut
)

router = APIRouter()


@router.get("/profile", response_model=APIResponse[Optional[BrandProfileOut]])
def get_brand_profile(
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """Retrieve the brand profile for the active organisation."""
    profile = db.query(BrandProfile).filter(BrandProfile.organisation_id == tenant.id).first()
    return APIResponse(
        success=True,
        data=BrandProfileOut.model_validate(profile) if profile else None
    )


@router.post("/profile", response_model=APIResponse[BrandProfileOut], status_code=status.HTTP_201_CREATED)
def create_brand_profile(
    payload: BrandProfileCreate,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Create initial brand profile for the active organisation (Admin or Brand Manager only)."""
    existing = db.query(BrandProfile).filter(BrandProfile.organisation_id == tenant.id).first()
    if existing:
        raise ConflictError("A brand profile already exists for this organisation. Use PATCH to update.")

    profile = BrandProfile(
        organisation_id=tenant.id,
        brand_name=payload.brand_name.strip(),
        industry=payload.industry.strip() if payload.industry else None,
        domain=payload.domain.strip() if payload.domain else None,
        description=payload.description.strip() if payload.description else None,
        brand_voice=payload.brand_voice.strip() if payload.brand_voice else None,
        target_audience=payload.target_audience.strip() if payload.target_audience else None,
        publishing_channels=payload.publishing_channels,
        applicable_regions=payload.applicable_regions
    )
    db.add(profile)
    db.flush()

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="BRAND_PROFILE_CREATED",
        entity_type="BRAND_PROFILE",
        entity_id=profile.id,
        metadata={"brand_name": profile.brand_name}
    )
    db.commit()
    db.refresh(profile)

    return APIResponse(
        success=True,
        message="Brand profile created successfully",
        data=BrandProfileOut.model_validate(profile)
    )


@router.patch("/profile", response_model=APIResponse[BrandProfileOut])
def update_brand_profile(
    payload: BrandProfileUpdate,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Update existing brand profile for the active organisation (Admin or Brand Manager only)."""
    profile = db.query(BrandProfile).filter(BrandProfile.organisation_id == tenant.id).first()
    if not profile:
        raise NotFoundError("Brand profile not found for this organisation. Create one first.")

    update_dict = payload.model_dump(exclude_unset=True)
    for field_name, value in update_dict.items():
        if isinstance(value, str):
            setattr(profile, field_name, value.strip() if value else None)
        else:
            setattr(profile, field_name, value)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="BRAND_PROFILE_UPDATED",
        entity_type="BRAND_PROFILE",
        entity_id=profile.id,
        metadata={"updated_fields": list(update_dict.keys())}
    )
    db.commit()
    db.refresh(profile)

    return APIResponse(
        success=True,
        message="Brand profile updated successfully",
        data=BrandProfileOut.model_validate(profile)
    )

