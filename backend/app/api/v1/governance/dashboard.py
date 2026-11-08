from fastapi import Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_tenant, get_current_user
from app.core.database import get_db
from app.models.organisation import Organisation
from app.models.content_submission import ContentSubmission
from app.models.review import (
    ReviewResult,
    ReviewOverallStatus,
    ReviewJob,
    ReviewJobStatus,
    Finding,
    FindingStatus,
    SeverityLevel,
)
from app.schemas.common import APIResponse
from .schemas import DashboardStats
from .router import router

@router.get("/dashboard", response_model=APIResponse[DashboardStats])
def get_dashboard(
    tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return organisation‑scoped governance metrics.
    All counts are computed live from the database; no hard‑coded numbers.
    """
    org_id = tenant.id

    total_submissions = (
        db.query(ContentSubmission)
        .filter(ContentSubmission.organisation_id == org_id)
        .count()
    )

    pending_reviews = (
        db.query(ReviewResult)
        .filter(ReviewResult.organisation_id == org_id)
        .filter(ReviewResult.overall_status == ReviewOverallStatus.INCOMPLETE.value)
        .count()
    )

    in_review = (
        db.query(ReviewJob)
        .filter(ReviewJob.organisation_id == org_id)
        .filter(
            ReviewJob.job_status.in_([
                ReviewJobStatus.PREPARING.value,
                ReviewJobStatus.READY_FOR_REVIEW.value,
            ])
        )
        .count()
    )

    changes_requested = (
        db.query(Finding)
        .filter(Finding.organisation_id == org_id)
        .filter(Finding.status == FindingStatus.REJECTED.value)
        .count()
    )

    approved = (
        db.query(ReviewResult)
        .filter(ReviewResult.organisation_id == org_id)
        .filter(ReviewResult.overall_status == ReviewOverallStatus.COMPLETED.value)
        .count()
    )

    rejected = (
        db.query(ReviewResult)
        .filter(ReviewResult.organisation_id == org_id)
        .filter(
            ReviewResult.overall_status.in_([
                ReviewOverallStatus.FAILED.value,
                ReviewOverallStatus.CANCELLED.value,
            ])
        )
        .count()
    )

    review_incomplete = pending_reviews

    high_risk_findings = (
        db.query(Finding)
        .filter(Finding.organisation_id == org_id)
        .filter(Finding.severity.in_([SeverityLevel.CRITICAL.value, SeverityLevel.HIGH.value]))
        .count()
    )

    stats = DashboardStats(
        total_submissions=total_submissions,
        pending_reviews=pending_reviews,
        in_review=in_review,
        changes_requested=changes_requested,
        approved=approved,
        rejected=rejected,
        review_incomplete=review_incomplete,
        high_risk_findings=high_risk_findings,
    )
    return APIResponse(success=True, data=stats)
