"""
Brand Knowledge Hub overview and analytics stats endpoint.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import (
    get_current_tenant,
    require_role
)
from app.models.user import Membership, RoleEnum
from app.models.organisation import Organisation
from app.models.brand_knowledge import (
    BrandDocument,
    ApprovedFact,
    TerminologyRule,
    DocumentChunk,
    ApprovalStatus
)
from app.schemas.common import APIResponse
from app.schemas.brand_knowledge import KnowledgeOverviewStats

router = APIRouter()


@router.get("/overview", response_model=APIResponse[KnowledgeOverviewStats])
def get_brand_knowledge_overview(
    tenant: Organisation = Depends(get_current_tenant),
    _role: Membership = Depends(require_role([RoleEnum.ADMIN, RoleEnum.BRAND_MANAGER, RoleEnum.CREATOR, RoleEnum.REVIEWER])),
    db: Session = Depends(get_db)
):
    """Retrieve real-time governance metrics and knowledge counts for active organisation."""
    # Documents
    total_docs = db.query(BrandDocument).filter(BrandDocument.organisation_id == tenant.id).count()
    approved_docs = db.query(BrandDocument).filter(
        BrandDocument.organisation_id == tenant.id,
        BrandDocument.approval_status == ApprovalStatus.APPROVED.value
    ).count()
    pending_docs = db.query(BrandDocument).filter(
        BrandDocument.organisation_id == tenant.id,
        BrandDocument.approval_status == ApprovalStatus.PENDING_APPROVAL.value
    ).count()

    # Facts
    total_facts = db.query(ApprovedFact).filter(ApprovedFact.organisation_id == tenant.id).count()
    approved_facts = db.query(ApprovedFact).filter(
        ApprovedFact.organisation_id == tenant.id,
        ApprovedFact.status == ApprovalStatus.APPROVED.value
    ).count()
    pending_facts = db.query(ApprovedFact).filter(
        ApprovedFact.organisation_id == tenant.id,
        ApprovedFact.status == ApprovalStatus.PENDING_APPROVAL.value
    ).count()

    # Terminology
    total_rules = db.query(TerminologyRule).filter(TerminologyRule.organisation_id == tenant.id).count()
    active_rules = db.query(TerminologyRule).filter(
        TerminologyRule.organisation_id == tenant.id,
        TerminologyRule.status == "ACTIVE"
    ).count()
    pending_rules = db.query(TerminologyRule).filter(
        TerminologyRule.organisation_id == tenant.id,
        TerminologyRule.status == "PENDING_APPROVAL"
    ).count()

    # Chunks
    total_chunks = db.query(DocumentChunk).filter(DocumentChunk.organisation_id == tenant.id).count()

    stats = KnowledgeOverviewStats(
        total_documents=total_docs,
        approved_documents=approved_docs,
        pending_documents=pending_docs,
        total_facts=total_facts,
        approved_facts=approved_facts,
        pending_facts=pending_facts,
        total_terminology_rules=total_rules,
        active_terminology_rules=active_rules,
        pending_terminology_rules=pending_rules,
        total_chunks=total_chunks
    )

    return APIResponse(success=True, data=stats)

