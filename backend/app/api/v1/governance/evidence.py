"""Governance evidence endpoint"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_tenant, get_current_user
from app.core.database import get_db
from app.models.organisation import Organisation
from app.models.review import FindingEvidence
from .schemas import EvidenceDetail, EvidenceResponse
from .router import router

@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
def get_evidence(
    evidence_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Read‑only preview of a finding evidence record.
    Validates organisation ownership and existence; raises 404 if not found.
    """
    evidence = (
        db.query(FindingEvidence)
        .filter(FindingEvidence.id == evidence_id)
        .filter(FindingEvidence.organisation_id == tenant.id)
        .first()
    )
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    detail = EvidenceDetail(
        id=evidence.id,
        finding_id=evidence.finding_id,
        document_id=evidence.document_id,
        document_version_id=evidence.document_version_id,
        chunk_id=evidence.chunk_id,
        source_quote=evidence.source_quote,
        source_page=evidence.source_page,
        source_location=evidence.source_location,
        relevance_metadata=evidence.relevance_metadata,
        verification_status=evidence.verification_status,
        created_at=evidence.created_at,
    )
    return EvidenceResponse(success=True, data=detail)
