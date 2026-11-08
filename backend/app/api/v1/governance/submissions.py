import hashlib
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.api.deps import get_current_tenant, get_current_user
from app.core.database import get_db
from app.models.organisation import Organisation
from app.models.user import User
from app.models.audit import AuditLog
from app.models.content_submission import ContentSubmission, ContentVersion, ReviewJob, ReviewJobStatus, SubmissionStatus
from app.models.review import (
    ReviewResult,
    ReviewOverallStatus,
    Finding,
    FindingStatus,
    FindingEvidence,
    Suggestion,
    SeverityLevel,
    ConfidenceLevel,
)
from app.ingestion.terminology_engine import TerminologyMatcher
from app.schemas.common import APIResponse
from .schemas import (
    SubmissionListItem,
    SubmissionsResponse,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionDetailResponse,
    ContentVersionDetail,
    ReviewResultDetail,
    FindingDetail,
    SuggestionDetail,
    EvidenceDetail,
    ReviewDecisionCreate,
    SuggestionAction,
)
from .router import router


@router.get("/submissions", response_model=SubmissionsResponse)
def list_submissions(
    # Filters
    search: Optional[str] = Query(None, description="Search in title or description"),
    status: Optional[str] = Query(None, description="SubmissionStatus filter"),
    channel: Optional[str] = Query(None, description="Publishing channel filter"),
    author_id: Optional[str] = Query(None, description="Creator user id filter"),
    start_date: Optional[datetime] = Query(None, description="Created after (inclusive)"),
    end_date: Optional[datetime] = Query(None, description="Created before (inclusive)"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="asc or desc"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List submissions with pagination and rich filtering."""
    query = db.query(ContentSubmission).filter(ContentSubmission.organisation_id == tenant.id)

    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(ContentSubmission.title.ilike(pattern), ContentSubmission.description.ilike(pattern)))
    if status:
        query = query.filter(ContentSubmission.current_status == status)
    if channel:
        query = query.filter(ContentSubmission.publishing_channel == channel)
    if author_id:
        query = query.filter(ContentSubmission.creator_id == author_id)
    if start_date:
        query = query.filter(ContentSubmission.created_at >= start_date)
    if end_date:
        query = query.filter(ContentSubmission.created_at <= end_date)

    # Sorting
    sort_column = getattr(ContentSubmission, sort_by, None)
    if not sort_column:
        raise HTTPException(status_code=400, detail="Invalid sort_by field")
    order_func = desc if sort_order.lower() == "desc" else asc
    query = query.order_by(order_func(sort_column))

    total = query.count()
    offset = (page - 1) * page_size
    rows = query.offset(offset).limit(page_size).all()

    items: List[SubmissionListItem] = []
    for sub in rows:
        rev = (
            db.query(ReviewResult)
            .filter(ReviewResult.submission_id == sub.id)
            .order_by(ReviewResult.created_at.desc())
            .first()
        )
        review_status = rev.overall_status if rev else None
        items.append(
            SubmissionListItem(
                id=sub.id,
                title=sub.title,
                content_type=sub.content_type,
                current_status=sub.current_status,
                publishing_channel=sub.publishing_channel,
                campaign_name=sub.campaign_name,
                target_audience=sub.target_audience,
                intended_publication_date=sub.intended_publication_date,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
                latest_review_status=review_status,
            )
        )

    total_pages = (total + page_size - 1) // page_size if total else 1
    return SubmissionsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/submissions", response_model=SubmissionDetailResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new content submission, version 1, and execute deterministic brand compliance checks."""
    sub = ContentSubmission(
        organisation_id=tenant.id,
        creator_id=current_user.id,
        title=payload.title,
        content_type=payload.content_type,
        publishing_channel=payload.publishing_channel,
        campaign_name=payload.campaign_name,
        target_audience=payload.target_audience,
        applicable_region=payload.applicable_region,
        language=payload.language,
        description=payload.description,
        current_status=SubmissionStatus.SUBMITTED.value,
        current_version_number=1,
    )
    db.add(sub)
    db.flush()

    # Content version 1
    text = payload.content_text
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    words = len(text.split())
    chars = len(text)

    ver = ContentVersion(
        organisation_id=tenant.id,
        submission_id=sub.id,
        version_number=1,
        content_text=text,
        content_hash=content_hash,
        word_count=words,
        character_count=chars,
        created_by=current_user.id,
    )
    db.add(ver)
    db.flush()

    # Create Review Job
    job = ReviewJob(
        organisation_id=tenant.id,
        submission_id=sub.id,
        content_version_id=ver.id,
        requested_by=current_user.id,
        idempotency_key=f"sub_{sub.id}_v1_{int(datetime.now(timezone.utc).timestamp())}",
        job_status=ReviewJobStatus.READY_FOR_REVIEW.value,
    )
    db.add(job)
    db.flush()

    # Create Review Result
    review_result = ReviewResult(
        organisation_id=tenant.id,
        review_job_id=job.id,
        submission_id=sub.id,
        content_version_id=ver.id,
        overall_status=ReviewOverallStatus.COMPLETED.value,
        findings_count=0,
        model_provider="BrandCanon-Deterministic-Engine",
        model_identifier="v1.0",
    )
    db.add(review_result)
    db.flush()

    # Execute deterministic terminology check
    matcher = TerminologyMatcher.from_organisation(db, tenant.id)
    matches = matcher.match_text(text)

    findings_count = 0
    for match in matches:
        finding = Finding(
            organisation_id=tenant.id,
            review_result_id=review_result.id,
            category="TERMINOLOGY",
            status=FindingStatus.DETECTED.value,
            severity=match.severity or SeverityLevel.HIGH.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            original_text=match.matched_text,
            start_offset=match.match_start,
            end_offset=match.match_end,
            explanation=f"Prohibited term '{match.prohibited_term}' detected. Use preferred term '{match.preferred_term}'. {match.description or ''}".strip(),
            verification_metadata={"rule_id": match.rule_id, "category": match.category},
        )
        db.add(finding)
        db.flush()

        suggestion = Suggestion(
            organisation_id=tenant.id,
            finding_id=finding.id,
            original_text=match.matched_text,
            suggested_text=match.preferred_term,
            reason=f"Brand terminology standard prefers '{match.preferred_term}' over prohibited '{match.prohibited_term}'",
            status="PENDING",
        )
        db.add(suggestion)
        findings_count += 1

    review_result.findings_count = findings_count
    if findings_count > 0:
        review_result.overall_status = ReviewOverallStatus.INCOMPLETE.value

    # Audit log
    audit = AuditLog(
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="SUBMISSION_CREATED",
        entity_type="CONTENT_SUBMISSION",
        entity_id=sub.id,
        metadata_json={
            "title": sub.title,
            "version": 1,
            "channel": sub.publishing_channel,
            "findings_count": findings_count,
        },
    )
    db.add(audit)
    db.commit()

    return get_submission_detail(sub.id, tenant, db, current_user)


@router.get("/submissions/{submission_id}", response_model=SubmissionDetailResponse)
def get_submission_detail(
    submission_id: str,
    tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full submission details with all versions and latest review results."""
    sub = (
        db.query(ContentSubmission)
        .filter(ContentSubmission.id == submission_id, ContentSubmission.organisation_id == tenant.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    versions_db = (
        db.query(ContentVersion)
        .filter(ContentVersion.submission_id == sub.id)
        .order_by(ContentVersion.version_number.desc())
        .all()
    )

    versions = [
        ContentVersionDetail(
            id=v.id,
            version_number=v.version_number,
            content_text=v.content_text,
            content_hash=v.content_hash,
            word_count=v.word_count,
            character_count=v.character_count,
            created_at=v.created_at,
        )
        for v in versions_db
    ]

    # Latest review result
    rev = (
        db.query(ReviewResult)
        .filter(ReviewResult.submission_id == sub.id)
        .order_by(ReviewResult.created_at.desc())
        .first()
    )

    review_result_detail = None
    if rev:
        findings_db = (
            db.query(Finding)
            .filter(Finding.review_result_id == rev.id)
            .order_by(Finding.start_offset.asc())
            .all()
        )
        findings = []
        for f in findings_db:
            sugg = db.query(Suggestion).filter(Suggestion.finding_id == f.id).first()
            sugg_detail = (
                SuggestionDetail(
                    id=sugg.id,
                    finding_id=sugg.finding_id,
                    original_text=sugg.original_text,
                    suggested_text=sugg.suggested_text,
                    reason=sugg.reason,
                    status=sugg.status,
                    created_at=sugg.created_at,
                )
                if sugg
                else None
            )

            evidences_db = db.query(FindingEvidence).filter(FindingEvidence.finding_id == f.id).all()
            evidences = [
                EvidenceDetail(
                    id=e.id,
                    finding_id=e.finding_id,
                    document_id=e.document_id,
                    document_version_id=e.document_version_id,
                    chunk_id=e.chunk_id,
                    source_quote=e.source_quote,
                    source_page=e.source_page,
                    source_location=e.source_location,
                    relevance_metadata=e.relevance_metadata,
                    verification_status=e.verification_status,
                    created_at=e.created_at,
                )
                for e in evidences_db
            ]

            findings.append(
                FindingDetail(
                    id=f.id,
                    category=f.category,
                    status=f.status,
                    severity=f.severity,
                    confidence_level=f.confidence_level,
                    original_text=f.original_text,
                    start_offset=f.start_offset,
                    end_offset=f.end_offset,
                    explanation=f.explanation,
                    suggestion=sugg_detail,
                    evidences=evidences,
                    created_at=f.created_at,
                )
            )

        review_result_detail = ReviewResultDetail(
            id=rev.id,
            overall_status=rev.overall_status,
            findings_count=rev.findings_count,
            model_provider=rev.model_provider,
            model_identifier=rev.model_identifier,
            findings=findings,
            created_at=rev.created_at,
        )

    detail = SubmissionDetail(
        id=sub.id,
        organisation_id=sub.organisation_id,
        creator_id=sub.creator_id,
        title=sub.title,
        content_type=sub.content_type,
        publishing_channel=sub.publishing_channel,
        campaign_name=sub.campaign_name,
        target_audience=sub.target_audience,
        applicable_region=sub.applicable_region,
        language=sub.language,
        description=sub.description,
        current_status=sub.current_status,
        current_version_number=sub.current_version_number,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
        versions=versions,
        latest_review_result=review_result_detail,
    )

    return SubmissionDetailResponse(success=True, data=detail)


@router.post("/submissions/{submission_id}/decide", response_model=SubmissionDetailResponse)
def record_review_decision(
    submission_id: str,
    payload: ReviewDecisionCreate,
    tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a formal governance decision (APPROVED, REQUEST_CHANGES, REJECTED) with audit logging."""
    sub = (
        db.query(ContentSubmission)
        .filter(ContentSubmission.id == submission_id, ContentSubmission.organisation_id == tenant.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    decision = payload.decision.upper()
    if decision not in ["APPROVED", "REQUEST_CHANGES", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid decision. Must be APPROVED, REQUEST_CHANGES, or REJECTED")

    if decision == "APPROVED":
        sub.current_status = "APPROVED"
    elif decision == "REQUEST_CHANGES":
        sub.current_status = "CHANGES_REQUESTED"
    else:
        sub.current_status = "REJECTED"

    # Update latest review result if present
    rev = (
        db.query(ReviewResult)
        .filter(ReviewResult.submission_id == sub.id)
        .order_by(ReviewResult.created_at.desc())
        .first()
    )
    if rev:
        if decision == "APPROVED":
            rev.overall_status = ReviewOverallStatus.COMPLETED.value
        elif decision == "REJECTED":
            rev.overall_status = ReviewOverallStatus.FAILED.value
        else:
            rev.overall_status = ReviewOverallStatus.INCOMPLETE.value

    # Record Audit
    audit = AuditLog(
        organisation_id=tenant.id,
        user_id=current_user.id,
        event_type="REVIEW_DECISION_RECORDED",
        entity_type="CONTENT_SUBMISSION",
        entity_id=sub.id,
        metadata_json={
            "decision": decision,
            "notes": payload.notes,
            "version_number": sub.current_version_number,
        },
    )
    db.add(audit)
    db.commit()

    return get_submission_detail(sub.id, tenant, db, current_user)


@router.post("/suggestions/{suggestion_id}/action", response_model=APIResponse[dict])
def handle_suggestion_action(
    suggestion_id: str,
    payload: SuggestionAction,
    tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply or reject an AI-generated suggestion. If applied, a new content version is created."""
    suggestion = (
        db.query(Suggestion)
        .filter(Suggestion.id == suggestion_id, Suggestion.organisation_id == tenant.id)
        .first()
    )
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    action = payload.action.upper()
    if action not in ["APPLY", "REJECT"]:
        raise HTTPException(status_code=400, detail="Action must be APPLY or REJECT")

    finding = db.query(Finding).filter(Finding.id == suggestion.finding_id).first()
    review_result = db.query(ReviewResult).filter(ReviewResult.id == finding.review_result_id).first() if finding else None
    submission = db.query(ContentSubmission).filter(ContentSubmission.id == review_result.submission_id).first() if review_result else None

    if action == "APPLY":
        suggestion.status = "APPLIED"
        if finding:
            finding.status = FindingStatus.VERIFIED.value

        if submission:
            # Fetch latest version to replace text
            latest_version = (
                db.query(ContentVersion)
                .filter(ContentVersion.submission_id == submission.id)
                .order_by(ContentVersion.version_number.desc())
                .first()
            )
            if latest_version:
                old_text = latest_version.content_text
                # Replace the exact occurrence of original_text
                new_text = old_text.replace(suggestion.original_text, suggestion.suggested_text, 1)
                new_version_num = latest_version.version_number + 1
                new_hash = hashlib.sha256(new_text.encode("utf-8")).hexdigest()

                new_ver = ContentVersion(
                    organisation_id=tenant.id,
                    submission_id=submission.id,
                    version_number=new_version_num,
                    content_text=new_text,
                    content_hash=new_hash,
                    word_count=len(new_text.split()),
                    character_count=len(new_text),
                    change_note=f"Applied suggestion: '{suggestion.original_text}' -> '{suggestion.suggested_text}'",
                    created_by=current_user.id,
                )
                db.add(new_ver)
                submission.current_version_number = new_version_num

        audit = AuditLog(
            organisation_id=tenant.id,
            user_id=current_user.id,
            event_type="SUGGESTION_APPLIED",
            entity_type="SUGGESTION",
            entity_id=suggestion.id,
            metadata_json={
                "original_text": suggestion.original_text,
                "suggested_text": suggestion.suggested_text,
            },
        )
        db.add(audit)
    else:
        suggestion.status = "REJECTED"
        if finding:
            finding.status = FindingStatus.REJECTED.value

        audit = AuditLog(
            organisation_id=tenant.id,
            user_id=current_user.id,
            event_type="SUGGESTION_REJECTED",
            entity_type="SUGGESTION",
            entity_id=suggestion.id,
            metadata_json={"original_text": suggestion.original_text},
        )
        db.add(audit)

    db.commit()
    return APIResponse(success=True, data={"suggestion_id": suggestion.id, "status": suggestion.status})
