import secrets
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password
from app.core.exceptions import (
    PermissionDeniedError,
    NotFoundError,
    ConflictError,
    ValidationError
)
from app.api.deps import (
    get_current_user,
    get_current_tenant,
    require_role,
    record_audit_log
)
from app.models.user import User, Membership, RoleEnum
from app.models.organisation import Organisation
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.member import MemberInvite, MemberRoleUpdate, MemberOut

router = APIRouter()


@router.get("", response_model=APIResponse[PaginatedResponse[MemberOut]])
def list_organisation_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """List members belonging to the current active workspace."""
    query = (
        db.query(Membership, User)
        .join(User, Membership.user_id == User.id)
        .filter(Membership.organisation_id == tenant.id)
        .order_by(Membership.created_at.asc())
    )

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    members_out = [
        MemberOut(
            id=m.id,
            user_id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=m.role,
            is_default=m.is_default,
            created_at=m.created_at
        )
        for m, u in items
    ]

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return APIResponse(
        success=True,
        data=PaginatedResponse(
            items=members_out,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.post("", response_model=APIResponse[MemberOut], status_code=status.HTTP_201_CREATED)
def invite_or_add_member(
    payload: MemberInvite,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _admin: Membership = Depends(require_role([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Add a new or existing user to the workspace with assigned role. Admin-only."""
    email_clean = payload.email.lower().strip()

    # Check if user already exists
    user = db.query(User).filter(User.email == email_clean).first()
    if not user:
        # Create user account
        temp_pwd = payload.initial_password or secrets.token_urlsafe(12)
        user = User(
            email=email_clean,
            hashed_password=hash_password(temp_pwd),
            full_name=payload.full_name.strip(),
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.flush()

    # Check if already a member of this organisation
    existing_membership = db.query(Membership).filter(
        Membership.organisation_id == tenant.id,
        Membership.user_id == user.id
    ).first()

    if existing_membership:
        raise ConflictError(f"User '{email_clean}' is already a member of this workspace")

    # Create membership
    new_membership = Membership(
        organisation_id=tenant.id,
        user_id=user.id,
        role=payload.role.value,
        is_default=False
    )
    db.add(new_membership)
    db.flush()

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="MEMBER_ADDED",
        entity_type="MEMBERSHIP",
        entity_id=new_membership.id,
        metadata={
            "member_email": email_clean,
            "role": payload.role.value,
            "added_by": current_user.email
        }
    )
    db.commit()
    db.refresh(new_membership)

    return APIResponse(
        success=True,
        message=f"Member '{email_clean}' added with role {payload.role.value}",
        data=MemberOut(
            id=new_membership.id,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=new_membership.role,
            is_default=new_membership.is_default,
            created_at=new_membership.created_at
        )
    )


@router.patch("/{member_id}/role", response_model=APIResponse[MemberOut])
def update_member_role(
    member_id: str,
    payload: MemberRoleUpdate,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _admin: Membership = Depends(require_role([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Change a member's role within the active organisation workspace. Admin-only."""
    target_membership = db.query(Membership).filter(
        Membership.id == member_id,
        Membership.organisation_id == tenant.id
    ).first()

    if not target_membership:
        raise NotFoundError(f"Membership '{member_id}' not found in current workspace")

    # Prevent demoting the last admin
    if target_membership.role == RoleEnum.ADMIN.value and payload.role.value != RoleEnum.ADMIN.value:
        admin_count = db.query(Membership).filter(
            Membership.organisation_id == tenant.id,
            Membership.role == RoleEnum.ADMIN.value
        ).count()
        if admin_count <= 1:
            raise ValidationError("Cannot demote the only remaining Workspace Admin")

    old_role = target_membership.role
    target_membership.role = payload.role.value

    user = db.query(User).filter(User.id == target_membership.user_id).first()

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="MEMBER_ROLE_UPDATED",
        entity_type="MEMBERSHIP",
        entity_id=target_membership.id,
        metadata={
            "member_email": user.email if user else None,
            "old_role": old_role,
            "new_role": payload.role.value
        }
    )
    db.commit()
    db.refresh(target_membership)

    return APIResponse(
        success=True,
        message="Member role updated successfully",
        data=MemberOut(
            id=target_membership.id,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=target_membership.role,
            is_default=target_membership.is_default,
            created_at=target_membership.created_at
        )
    )


@router.delete("/{member_id}", response_model=APIResponse[dict])
def remove_member(
    member_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _admin: Membership = Depends(require_role([RoleEnum.ADMIN])),
    db: Session = Depends(get_db)
):
    """Remove a member from the workspace. Admin-only."""
    target_membership = db.query(Membership).filter(
        Membership.id == member_id,
        Membership.organisation_id == tenant.id
    ).first()

    if not target_membership:
        raise NotFoundError("Membership not found in current workspace")

    # Prevent deleting the last admin
    if target_membership.role == RoleEnum.ADMIN.value:
        admin_count = db.query(Membership).filter(
            Membership.organisation_id == tenant.id,
            Membership.role == RoleEnum.ADMIN.value
        ).count()
        if admin_count <= 1:
            raise ValidationError("Cannot remove the only remaining Workspace Admin")

    user = db.query(User).filter(User.id == target_membership.user_id).first()
    user_email = user.email if user else "unknown"

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="MEMBER_REMOVED",
        entity_type="MEMBERSHIP",
        entity_id=target_membership.id,
        metadata={"removed_email": user_email}
    )

    db.delete(target_membership)
    db.commit()

    return APIResponse(
        success=True,
        message=f"Member '{user_email}' removed from workspace",
        data={"member_id": member_id}
    )

