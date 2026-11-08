"""
Knowledge Approvals audit and history API endpoints.
Provides review queue visibility and historical approval/rejection audit trail.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.api.deps import (
    get_current_tenant,
    require_role
)
from app.models.user import Membership, RoleEnum
from app.models.organisation import Organisation
from app.models.brand_knowledge import KnowledgeApproval
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.brand_knowledge import KnowledgeApprovalOut

router = APIRouter()


@router.get("/approvals", response_model=APIResponse[PaginatedResponse[KnowledgeApprovalOut]])
def list_knowledge_approvals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = Query(None),
    decision: Optional[str] = Query(None),
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """List historical knowledge approvals, rejections, and archival decisions."""
    query = db.query(KnowledgeApproval).filter(KnowledgeApproval.organisation_id == tenant.id)

    if entity_type:
        query = query.filter(KnowledgeApproval.entity_type == entity_type)
    if decision:
        query = query.filter(KnowledgeApproval.decision == decision)

    total = query.count()
    items = query.order_by(KnowledgeApproval.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    approvals_out = [KnowledgeApprovalOut.model_validate(a) for a in items]

    return APIResponse(
        success=True,
        data=PaginatedResponse(
            items=approvals_out,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/approvals/{approval_id}", response_model=APIResponse[KnowledgeApprovalOut])
def get_knowledge_approval(
    approval_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """Get single knowledge approval decision record."""
    item = db.query(KnowledgeApproval).filter(
        KnowledgeApproval.id == approval_id,
        KnowledgeApproval.organisation_id == tenant.id
    ).first()

    if not item:
        raise NotFoundError("Approval record not found")

    return APIResponse(success=True, data=KnowledgeApprovalOut.model_validate(item))

