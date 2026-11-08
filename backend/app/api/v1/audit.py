from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_tenant,
    require_role
)
from app.models.user import Membership, RoleEnum
from app.models.organisation import Organisation
from app.models.audit import AuditLog
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.audit import AuditLogOut

router = APIRouter()


@router.get("", response_model=APIResponse[PaginatedResponse[AuditLogOut]])
def list_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Retrieve organisation-scoped audit trails. Accessible to Admins and Brand Managers."""
    query = db.query(AuditLog).filter(AuditLog.organisation_id == tenant.id)

    if event_type:
        query = query.filter(AuditLog.event_type == event_type.strip())
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type.strip())

    total = query.count()
    items = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items_out = [
        AuditLogOut(
            id=log.id,
            organisation_id=log.organisation_id,
            user_id=log.user_id,
            event_type=log.event_type,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            metadata_json=log.metadata_json or {},
            created_at=log.created_at
        )
        for log in items
    ]

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return APIResponse(
        success=True,
        data=PaginatedResponse(
            items=items_out,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )

