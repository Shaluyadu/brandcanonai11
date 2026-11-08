import re
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_user,
    get_current_tenant,
    get_current_membership,
    require_role,
    record_audit_log
)
from app.models.user import User, Membership, RoleEnum
from app.models.organisation import Organisation, OrganisationSettings
from app.schemas.common import APIResponse
from app.schemas.organisation import (
    OrganisationCreate,
    OrganisationUpdate,
    OrganisationOut,
    OrganisationDetailOut,
    OrganisationSettingsOut,
    OrganisationSettingsUpdate
)

router = APIRouter()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


@router.get("/current", response_model=APIResponse[OrganisationDetailOut])
def get_current_organisation_details(
    tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    """Retrieve details and governance settings of the currently active workspace."""
    settings = db.query(OrganisationSettings).filter(
        OrganisationSettings.organisation_id == tenant.id
    ).first()

    settings_out = OrganisationSettingsOut.model_validate(settings) if settings else None

    detail = OrganisationDetailOut(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        industry=tenant.industry,
        domain=tenant.domain,
        is_active=tenant.is_active,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        settings=settings_out
    )

    return APIResponse(success=True, data=detail)


@router.patch("/current", response_model=APIResponse[OrganisationDetailOut])
def update_current_organisation(
    payload: OrganisationUpdate,
    tenant: Organisation = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Update active workspace metadata. Accessible to Admins and Brand Managers."""
    if payload.name is not None and payload.name.strip():
        tenant.name = payload.name.strip()
    if payload.industry is not None:
        tenant.industry = payload.industry.strip()
    if payload.domain is not None:
        tenant.domain = payload.domain.strip()

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=user.id,
        event_type="ORGANISATION_UPDATED",
        entity_type="ORGANISATION",
        entity_id=tenant.id,
        metadata={"updated_fields": [k for k, v in payload.model_dump(exclude_unset=True).items()]}
    )
    db.commit()
    db.refresh(tenant)

    settings = db.query(OrganisationSettings).filter(
        OrganisationSettings.organisation_id == tenant.id
    ).first()

    return APIResponse(
        success=True,
        message="Workspace updated successfully",
        data=OrganisationDetailOut(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            industry=tenant.industry,
            domain=tenant.domain,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
            settings=OrganisationSettingsOut.model_validate(settings) if settings else None
        )
    )


@router.patch("/current/settings", response_model=APIResponse[OrganisationSettingsOut])
def update_organisation_settings(
    payload: OrganisationSettingsUpdate,
    tenant: Organisation = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update workspace governance enforcement settings. Admin-only."""
    settings = db.query(OrganisationSettings).filter(
        OrganisationSettings.organisation_id == tenant.id
    ).first()

    if not settings:
        settings = OrganisationSettings(
            organisation_id=tenant.id,
            enforce_brand_voice=True,
            strict_mode=False,
            custom_metadata={}
        )
        db.add(settings)

    if payload.enforce_brand_voice is not None:
        settings.enforce_brand_voice = payload.enforce_brand_voice
    if payload.strict_mode is not None:
        settings.strict_mode = payload.strict_mode
    if payload.custom_metadata is not None:
        settings.custom_metadata = payload.custom_metadata

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=user.id,
        event_type="SETTINGS_UPDATED",
        entity_type="ORGANISATION_SETTINGS",
        entity_id=settings.id,
        metadata=payload.model_dump(exclude_unset=True)
    )
    db.commit()
    db.refresh(settings)

    return APIResponse(
        success=True,
        message="Settings updated successfully",
        data=OrganisationSettingsOut.model_validate(settings)
    )


@router.post("", response_model=APIResponse[OrganisationOut], status_code=status.HTTP_201_CREATED)
def create_organisation_workspace(
    payload: OrganisationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new organisation workspace and assign current user as ADMIN."""
    org_name = payload.name.strip()
    base_slug = slugify(payload.slug or org_name)
    slug = base_slug
    counter = 1
    while db.query(Organisation).filter(Organisation.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    new_org = Organisation(
        name=org_name,
        slug=slug,
        industry=payload.industry.strip() if payload.industry else None,
        domain=payload.domain.strip() if payload.domain else None,
        is_active=True
    )
    db.add(new_org)
    db.flush()

    settings = OrganisationSettings(
        organisation_id=new_org.id,
        enforce_brand_voice=True,
        strict_mode=False,
        custom_metadata={}
    )
    db.add(settings)
    db.flush()

    membership = Membership(
        organisation_id=new_org.id,
        user_id=user.id,
        role=RoleEnum.ADMIN.value,
        is_default=False
    )
    db.add(membership)
    db.flush()

    record_audit_log(
        db=db,
        organisation_id=new_org.id,
        user_id=user.id,
        event_type="WORKSPACE_CREATED",
        entity_type="ORGANISATION",
        entity_id=new_org.id,
        metadata={"name": org_name, "slug": slug}
    )
    db.commit()
    db.refresh(new_org)

    return APIResponse(
        success=True,
        message="New organisation workspace created successfully",
        data=OrganisationOut.model_validate(new_org)
    )

