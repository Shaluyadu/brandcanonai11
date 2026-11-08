"""
Approved Facts & Claims API endpoints.
Manage verified product specifications, claims, and approval lifecycle.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.api.deps import (
    get_current_user,
    get_current_tenant,
    require_role,
    record_audit_log
)
from app.models.user import User, Membership, RoleEnum
from app.models.organisation import Organisation
from app.models.brand_knowledge import (
    ApprovedFact,
    BrandDocument,
    KnowledgeApproval,
    ApprovalStatus
)
from app.models.base import utc_now, generate_uuid
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.brand_knowledge import (
    ApprovedFactCreate,
    ApprovedFactUpdate,
    ApprovedFactOut,
    ApprovalDecisionRequest
)

router = APIRouter()


@router.post("/facts", response_model=APIResponse[ApprovedFactOut], status_code=status.HTTP_201_CREATED)
def create_approved_fact(
    payload: ApprovedFactCreate,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR])),
    db: Session = Depends(get_db)
):
    """
    Create a new brand fact or specification claim.
    Requires Admin or Brand Manager approval before it becomes active in knowledge retrieval.
    """
    if payload.brand_document_id:
        doc = db.query(BrandDocument).filter(
            BrandDocument.id == payload.brand_document_id,
            BrandDocument.organisation_id == tenant.id
        ).first()
        if not doc:
            raise ValidationError("Referenced source document does not exist in this organisation")

    fact = ApprovedFact(
        id=generate_uuid(),
        organisation_id=tenant.id,
        brand_document_id=payload.brand_document_id,
        title=payload.title.strip(),
        claim_text=payload.claim_text.strip(),
        category=payload.category,
        evidence_quote=payload.evidence_quote.strip() if payload.evidence_quote else None,
        source_page=payload.source_page,
        source_location=payload.source_location.strip() if payload.source_location else None,
        applicable_region=payload.applicable_region,
        applicable_audience=payload.applicable_audience,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        status=ApprovalStatus.PENDING_APPROVAL.value,
        created_by=current_user.id
    )
    db.add(fact)
    db.flush()

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="FACT_CREATED",
        entity_type="APPROVED_FACT",
        entity_id=fact.id,
        metadata={"title": fact.title, "category": fact.category}
    )
    db.commit()
    db.refresh(fact)

    return APIResponse(
        success=True,
        message="Fact submitted for approval",
        data=ApprovedFactOut.model_validate(fact)
    )


@router.get("/facts", response_model=APIResponse[PaginatedResponse[ApprovedFactOut]])
def list_approved_facts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """List approved facts and claims in the workspace with pagination and filters."""
    query = db.query(ApprovedFact).filter(ApprovedFact.organisation_id == tenant.id)

    if status_filter:
        query = query.filter(ApprovedFact.status == status_filter)
    if category:
        query = query.filter(ApprovedFact.category == category)

    total = query.count()
    items = query.order_by(ApprovedFact.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    facts_out = [ApprovedFactOut.model_validate(f) for f in items]

    return APIResponse(
        success=True,
        data=PaginatedResponse(
            items=facts_out,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/facts/{fact_id}", response_model=APIResponse[ApprovedFactOut])
def get_approved_fact(
    fact_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """Get single fact details."""
    fact = db.query(ApprovedFact).filter(
        ApprovedFact.id == fact_id,
        ApprovedFact.organisation_id == tenant.id
    ).first()

    if not fact:
        raise NotFoundError("Fact not found in workspace")

    return APIResponse(success=True, data=ApprovedFactOut.model_validate(fact))


@router.patch("/facts/{fact_id}", response_model=APIResponse[ApprovedFactOut])
def update_approved_fact(
    fact_id: str,
    payload: ApprovedFactUpdate,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Update fact details (Admin or Brand Manager only)."""
    fact = db.query(ApprovedFact).filter(
        ApprovedFact.id == fact_id,
        ApprovedFact.organisation_id == tenant.id
    ).first()

    if not fact:
        raise NotFoundError("Fact not found in workspace")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        if isinstance(v, str):
            setattr(fact, k, v.strip() if v else None)
        else:
            setattr(fact, k, v)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="FACT_UPDATED",
        entity_type="APPROVED_FACT",
        entity_id=fact.id,
        metadata={"updated_fields": list(update_dict.keys())}
    )
    db.commit()
    db.refresh(fact)

    return APIResponse(
        success=True,
        message="Fact updated successfully",
        data=ApprovedFactOut.model_validate(fact)
    )


@router.post("/facts/{fact_id}/approve", response_model=APIResponse[ApprovedFactOut])
def approve_fact(
    fact_id: str,
    payload: ApprovalDecisionRequest,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Approve a fact to make it active in the organisational knowledge base."""
    if payload.decision != "APPROVED":
        raise ValidationError("Decision must be 'APPROVED' for this endpoint")

    fact = db.query(ApprovedFact).filter(
        ApprovedFact.id == fact_id,
        ApprovedFact.organisation_id == tenant.id
    ).first()

    if not fact:
        raise NotFoundError("Fact not found in workspace")

    fact.status = ApprovalStatus.APPROVED.value
    fact.approved_by = current_user.id
    fact.approved_at = utc_now()

    approval = KnowledgeApproval(
        id=generate_uuid(),
        organisation_id=tenant.id,
        entity_type="FACT",
        entity_id=fact.id,
        decision="APPROVED",
        reviewer_id=current_user.id,
        reason=payload.reason
    )
    db.add(approval)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="FACT_APPROVED",
        entity_type="APPROVED_FACT",
        entity_id=fact.id,
        metadata={"reason": payload.reason}
    )
    db.commit()
    db.refresh(fact)

    return APIResponse(
        success=True,
        message="Fact approved successfully",
        data=ApprovedFactOut.model_validate(fact)
    )


@router.post("/facts/{fact_id}/reject", response_model=APIResponse[ApprovedFactOut])
def reject_fact(
    fact_id: str,
    payload: ApprovalDecisionRequest,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Reject a fact (excluded from active knowledge base)."""
    if payload.decision != "REJECTED":
        raise ValidationError("Decision must be 'REJECTED' for this endpoint")

    fact = db.query(ApprovedFact).filter(
        ApprovedFact.id == fact_id,
        ApprovedFact.organisation_id == tenant.id
    ).first()

    if not fact:
        raise NotFoundError("Fact not found in workspace")

    fact.status = ApprovalStatus.REJECTED.value

    approval = KnowledgeApproval(
        id=generate_uuid(),
        organisation_id=tenant.id,
        entity_type="FACT",
        entity_id=fact.id,
        decision="REJECTED",
        reviewer_id=current_user.id,
        reason=payload.reason
    )
    db.add(approval)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="FACT_REJECTED",
        entity_type="APPROVED_FACT",
        entity_id=fact.id,
        metadata={"reason": payload.reason}
    )
    db.commit()
    db.refresh(fact)

    return APIResponse(
        success=True,
        message="Fact rejected",
        data=ApprovedFactOut.model_validate(fact)
    )


@router.post("/facts/{fact_id}/archive", response_model=APIResponse[ApprovedFactOut])
def archive_fact(
    fact_id: str,
    payload: ApprovalDecisionRequest,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Archive a fact (retires fact from active knowledge)."""
    if payload.decision != "ARCHIVED":
        raise ValidationError("Decision must be 'ARCHIVED' for this endpoint")

    fact = db.query(ApprovedFact).filter(
        ApprovedFact.id == fact_id,
        ApprovedFact.organisation_id == tenant.id
    ).first()

    if not fact:
        raise NotFoundError("Fact not found in workspace")

    fact.status = ApprovalStatus.ARCHIVED.value

    approval = KnowledgeApproval(
        id=generate_uuid(),
        organisation_id=tenant.id,
        entity_type="FACT",
        entity_id=fact.id,
        decision="ARCHIVED",
        reviewer_id=current_user.id,
        reason=payload.reason
    )
    db.add(approval)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="FACT_ARCHIVED",
        entity_type="APPROVED_FACT",
        entity_id=fact.id,
        metadata={"reason": payload.reason}
    )
    db.commit()
    db.refresh(fact)

    return APIResponse(
        success=True,
        message="Fact archived",
        data=ApprovedFactOut.model_validate(fact)
    )


@router.delete("/facts/{fact_id}", response_model=APIResponse[dict])
def delete_fact(
    fact_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Delete a fact from the workspace."""
    fact = db.query(ApprovedFact).filter(
        ApprovedFact.id == fact_id,
        ApprovedFact.organisation_id == tenant.id
    ).first()

    if not fact:
        raise NotFoundError("Fact not found in workspace")

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="FACT_DELETED",
        entity_type="APPROVED_FACT",
        entity_id=fact.id,
        metadata={"title": fact.title}
    )

    db.delete(fact)
    db.commit()

    return APIResponse(
        success=True,
        message="Fact deleted successfully",
        data={"fact_id": fact_id}
    )

