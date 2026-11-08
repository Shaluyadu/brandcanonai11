"""
Terminology Rules API endpoints.
Manage preferred and prohibited terms, matching criteria, severity, and interactive checking.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
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
    TerminologyRule,
    KnowledgeApproval,
    BrandDocument
)
from app.models.base import utc_now, generate_uuid
from app.schemas.common import APIResponse, PaginatedResponse
from app.schemas.brand_knowledge import (
    TerminologyRuleCreate,
    TerminologyRuleUpdate,
    TerminologyRuleOut,
    ApprovalDecisionRequest
)
from app.ingestion.terminology_engine import TerminologyMatcher

router = APIRouter()


class TerminologyCheckRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TerminologyMatchResult(BaseModel):
    rule_id: str
    prohibited_term: str
    preferred_term: str
    match_start: int
    match_end: int
    matched_text: str
    severity: str
    category: str
    match_type: str
    description: Optional[str] = None


@router.post("/terminology", response_model=APIResponse[TerminologyRuleOut], status_code=status.HTTP_201_CREATED)
def create_terminology_rule(
    payload: TerminologyRuleCreate,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """
    Create a new terminology rule.
    By default, Brand Managers create rules directly with ACTIVE status or PENDING_APPROVAL.
    """
    if payload.source_document_id:
        doc = db.query(BrandDocument).filter(
            BrandDocument.id == payload.source_document_id,
            BrandDocument.organisation_id == tenant.id
        ).first()
        if not doc:
            raise ValidationError("Referenced source document does not exist in this organisation")

    rule = TerminologyRule(
        id=generate_uuid(),
        organisation_id=tenant.id,
        preferred_term=payload.preferred_term.strip(),
        prohibited_term=payload.prohibited_term.strip(),
        description=payload.description.strip() if payload.description else None,
        match_type=payload.match_type,
        case_sensitive=payload.case_sensitive,
        category=payload.category,
        severity=payload.severity,
        applicable_channel=payload.applicable_channel,
        applicable_region=payload.applicable_region,
        status="ACTIVE",
        source_document_id=payload.source_document_id,
        created_by=current_user.id,
        approved_by=current_user.id,
        approved_at=utc_now()
    )
    db.add(rule)
    db.flush()

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="TERMINOLOGY_RULE_CREATED",
        entity_type="TERMINOLOGY_RULE",
        entity_id=rule.id,
        metadata={
            "prohibited_term": rule.prohibited_term,
            "preferred_term": rule.preferred_term,
            "match_type": rule.match_type
        }
    )
    db.commit()
    db.refresh(rule)

    return APIResponse(
        success=True,
        message="Terminology rule created successfully",
        data=TerminologyRuleOut.model_validate(rule)
    )


@router.get("/terminology", response_model=APIResponse[PaginatedResponse[TerminologyRuleOut]])
def list_terminology_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """List terminology rules in the workspace with pagination and filters."""
    query = db.query(TerminologyRule).filter(TerminologyRule.organisation_id == tenant.id)

    if status_filter:
        query = query.filter(TerminologyRule.status == status_filter)
    if category:
        query = query.filter(TerminologyRule.category == category)
    if severity:
        query = query.filter(TerminologyRule.severity == severity)

    total = query.count()
    items = query.order_by(TerminologyRule.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    rules_out = [TerminologyRuleOut.model_validate(r) for r in items]

    return APIResponse(
        success=True,
        data=PaginatedResponse(
            items=rules_out,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.get("/terminology/{rule_id}", response_model=APIResponse[TerminologyRuleOut])
def get_terminology_rule(
    rule_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """Get single terminology rule details."""
    rule = db.query(TerminologyRule).filter(
        TerminologyRule.id == rule_id,
        TerminologyRule.organisation_id == tenant.id
    ).first()

    if not rule:
        raise NotFoundError("Terminology rule not found in workspace")

    return APIResponse(success=True, data=TerminologyRuleOut.model_validate(rule))


@router.patch("/terminology/{rule_id}", response_model=APIResponse[TerminologyRuleOut])
def update_terminology_rule(
    rule_id: str,
    payload: TerminologyRuleUpdate,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Update terminology rule details (Admin or Brand Manager only)."""
    rule = db.query(TerminologyRule).filter(
        TerminologyRule.id == rule_id,
        TerminologyRule.organisation_id == tenant.id
    ).first()

    if not rule:
        raise NotFoundError("Terminology rule not found in workspace")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        if isinstance(v, str):
            setattr(rule, k, v.strip() if v else None)
        else:
            setattr(rule, k, v)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="TERMINOLOGY_RULE_UPDATED",
        entity_type="TERMINOLOGY_RULE",
        entity_id=rule.id,
        metadata={"updated_fields": list(update_dict.keys())}
    )
    db.commit()
    db.refresh(rule)

    return APIResponse(
        success=True,
        message="Terminology rule updated successfully",
        data=TerminologyRuleOut.model_validate(rule)
    )


@router.post("/terminology/{rule_id}/approve", response_model=APIResponse[TerminologyRuleOut])
def approve_terminology_rule(
    rule_id: str,
    payload: ApprovalDecisionRequest,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Approve a terminology rule to activate it."""
    if payload.decision != "APPROVED":
        raise ValidationError("Decision must be 'APPROVED' for this endpoint")

    rule = db.query(TerminologyRule).filter(
        TerminologyRule.id == rule_id,
        TerminologyRule.organisation_id == tenant.id
    ).first()

    if not rule:
        raise NotFoundError("Terminology rule not found in workspace")

    rule.status = "ACTIVE"
    rule.approved_by = current_user.id
    rule.approved_at = utc_now()

    approval = KnowledgeApproval(
        id=generate_uuid(),
        organisation_id=tenant.id,
        entity_type="TERMINOLOGY_RULE",
        entity_id=rule.id,
        decision="APPROVED",
        reviewer_id=current_user.id,
        reason=payload.reason
    )
    db.add(approval)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="TERMINOLOGY_RULE_APPROVED",
        entity_type="TERMINOLOGY_RULE",
        entity_id=rule.id,
        metadata={"reason": payload.reason}
    )
    db.commit()
    db.refresh(rule)

    return APIResponse(
        success=True,
        message="Terminology rule activated",
        data=TerminologyRuleOut.model_validate(rule)
    )


@router.post("/terminology/{rule_id}/reject", response_model=APIResponse[TerminologyRuleOut])
def reject_terminology_rule(
    rule_id: str,
    payload: ApprovalDecisionRequest,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Reject a terminology rule."""
    if payload.decision != "REJECTED":
        raise ValidationError("Decision must be 'REJECTED' for this endpoint")

    rule = db.query(TerminologyRule).filter(
        TerminologyRule.id == rule_id,
        TerminologyRule.organisation_id == tenant.id
    ).first()

    if not rule:
        raise NotFoundError("Terminology rule not found in workspace")

    rule.status = "REJECTED"

    approval = KnowledgeApproval(
        id=generate_uuid(),
        organisation_id=tenant.id,
        entity_type="TERMINOLOGY_RULE",
        entity_id=rule.id,
        decision="REJECTED",
        reviewer_id=current_user.id,
        reason=payload.reason
    )
    db.add(approval)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="TERMINOLOGY_RULE_REJECTED",
        entity_type="TERMINOLOGY_RULE",
        entity_id=rule.id,
        metadata={"reason": payload.reason}
    )
    db.commit()
    db.refresh(rule)

    return APIResponse(
        success=True,
        message="Terminology rule rejected",
        data=TerminologyRuleOut.model_validate(rule)
    )


@router.post("/terminology/{rule_id}/archive", response_model=APIResponse[TerminologyRuleOut])
def archive_terminology_rule(
    rule_id: str,
    payload: ApprovalDecisionRequest,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Archive a terminology rule."""
    if payload.decision != "ARCHIVED":
        raise ValidationError("Decision must be 'ARCHIVED' for this endpoint")

    rule = db.query(TerminologyRule).filter(
        TerminologyRule.id == rule_id,
        TerminologyRule.organisation_id == tenant.id
    ).first()

    if not rule:
        raise NotFoundError("Terminology rule not found in workspace")

    rule.status = "ARCHIVED"

    approval = KnowledgeApproval(
        id=generate_uuid(),
        organisation_id=tenant.id,
        entity_type="TERMINOLOGY_RULE",
        entity_id=rule.id,
        decision="ARCHIVED",
        reviewer_id=current_user.id,
        reason=payload.reason
    )
    db.add(approval)

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="TERMINOLOGY_RULE_ARCHIVED",
        entity_type="TERMINOLOGY_RULE",
        entity_id=rule.id,
        metadata={"reason": payload.reason}
    )
    db.commit()
    db.refresh(rule)

    return APIResponse(
        success=True,
        message="Terminology rule archived",
        data=TerminologyRuleOut.model_validate(rule)
    )


@router.delete("/terminology/{rule_id}", response_model=APIResponse[dict])
def delete_terminology_rule(
    rule_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER])),
    db: Session = Depends(get_db)
):
    """Delete a terminology rule."""
    rule = db.query(TerminologyRule).filter(
        TerminologyRule.id == rule_id,
        TerminologyRule.organisation_id == tenant.id
    ).first()

    if not rule:
        raise NotFoundError("Terminology rule not found in workspace")

    record_audit_log(
        db=db,
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="TERMINOLOGY_RULE_DELETED",
        entity_type="TERMINOLOGY_RULE",
        entity_id=rule.id,
        metadata={"prohibited_term": rule.prohibited_term}
    )

    db.delete(rule)
    db.commit()

    return APIResponse(
        success=True,
        message="Terminology rule deleted successfully",
        data={"rule_id": rule_id}
    )


@router.post("/terminology/check", response_model=APIResponse[List[TerminologyMatchResult]])
def check_text_terminology(
    payload: TerminologyCheckRequest,
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """
    Check input text against active organisation terminology rules.
    Returns matched prohibited terms, positions, and recommended preferred replacements.
    """
    matcher = TerminologyMatcher.from_organisation(db=db, organisation_id=tenant.id)
    matches = matcher.match_text(payload.text)

    results = [
        TerminologyMatchResult(
            rule_id=m.rule_id,
            prohibited_term=m.prohibited_term,
            preferred_term=m.preferred_term,
            match_start=m.match_start,
            match_end=m.match_end,
            matched_text=m.matched_text,
            severity=m.severity,
            category=m.category,
            match_type=m.match_type,
            description=m.description
        )
        for m in matches
    ]

    return APIResponse(
        success=True,
        message=f"Found {len(results)} terminology match(es)",
        data=results
    )

