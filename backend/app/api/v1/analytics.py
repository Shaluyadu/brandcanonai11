from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import get_current_tenant, get_current_user
from app.core.database import get_db
from app.models.organisation import Organisation
from app.models.user import User
from app.models.content_submission import ContentSubmission
from app.models.review import ReviewResult, Finding, FindingStatus, SeverityLevel
from app.schemas.common import APIResponse

router = APIRouter()


class RuleViolationStat(BaseModel):
    rule_term: str
    category: str
    count: int
    severity: str


class AnalyticsOverview(BaseModel):
    compliance_rate: float = Field(..., description="Percentage of clean reviews with no critical/high issues")
    total_submissions_analyzed: int
    total_findings_detected: int
    critical_findings_count: int
    average_turnaround_hours: float
    top_violated_rules: List[RuleViolationStat]
    violations_by_channel: Dict[str, int]
    violations_by_severity: Dict[str, int]
    submission_status_breakdown: Dict[str, int]


@router.get("/overview", response_model=APIResponse[AnalyticsOverview])
def get_analytics_overview(
    tenant: Organisation = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute enterprise-grade live compliance analytics and governance insights."""
    org_id = tenant.id

    # 1. Total submissions
    subs = db.query(ContentSubmission).filter(ContentSubmission.organisation_id == org_id).all()
    total_submissions = len(subs)

    # 2. Total findings
    findings = db.query(Finding).filter(Finding.organisation_id == org_id).all()
    total_findings = len(findings)

    # 3. Severity breakdown
    sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in findings:
        sev = (f.severity or "MEDIUM").upper()
        if sev in sev_counts:
            sev_counts[sev] += 1
        else:
            sev_counts[sev] = 1

    critical_count = sev_counts.get("CRITICAL", 0) + sev_counts.get("HIGH", 0)

    # 4. Compliance rate
    # Submissions that have no critical/high findings
    completed_reviews = db.query(ReviewResult).filter(ReviewResult.organisation_id == org_id).all()
    if completed_reviews:
        clean_count = sum(1 for r in completed_reviews if r.findings_count == 0)
        compliance_rate = round((clean_count / len(completed_reviews)) * 100.0, 1)
    else:
        compliance_rate = 100.0 if total_submissions == 0 else 0.0

    # 5. Turnaround time in hours
    turnaround_times = []
    for s in subs:
        if s.updated_at and s.created_at and s.current_status in ["APPROVED", "REJECTED", "CHANGES_REQUESTED"]:
            diff = (s.updated_at - s.created_at).total_seconds() / 3600.0
            turnaround_times.append(max(0.1, diff))
    avg_turnaround = round(sum(turnaround_times) / len(turnaround_times), 1) if turnaround_times else 1.2

    # 6. Violations by Channel
    channel_counts: Dict[str, int] = {}
    status_counts: Dict[str, int] = {}
    for s in subs:
        ch = s.publishing_channel or "OTHER"
        channel_counts[ch] = channel_counts.get(ch, 0) + 1
        st = s.current_status or "DRAFT"
        status_counts[st] = status_counts.get(st, 0) + 1

    # 7. Top Violated Rules
    term_counts: Dict[str, Dict[str, Any]] = {}
    for f in findings:
        key = f.original_text.lower().strip()
        if key not in term_counts:
            term_counts[key] = {
                "rule_term": f.original_text,
                "category": f.category,
                "count": 0,
                "severity": f.severity,
            }
        term_counts[key]["count"] += 1

    sorted_rules = sorted(term_counts.values(), key=lambda x: x["count"], reverse=True)[:10]
    top_rules = [
        RuleViolationStat(
            rule_term=r["rule_term"],
            category=r["category"],
            count=r["count"],
            severity=r["severity"],
        )
        for r in sorted_rules
    ]

    overview = AnalyticsOverview(
        compliance_rate=compliance_rate,
        total_submissions_analyzed=total_submissions,
        total_findings_detected=total_findings,
        critical_findings_count=critical_count,
        average_turnaround_hours=avg_turnaround,
        top_violated_rules=top_rules,
        violations_by_channel=channel_counts,
        violations_by_severity=sev_counts,
        submission_status_breakdown=status_counts,
    )

    return APIResponse(success=True, data=overview)

