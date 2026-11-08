import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.content_submission import ContentSubmission, ContentVersion
from app.models.review import ReviewResult, ReviewOverallStatus, Finding, FindingStatus, SeverityLevel, FindingEvidence, Suggestion
from app.models.brand_knowledge import TerminologyRule, TerminologyMatchType, TerminologySeverity


def make_submission(db: Session, org, user, title="Test", status="SUBMITTED"):
    sub = ContentSubmission(
        organisation_id=org.id,
        creator_id=user.id,
        title=title,
        content_type="ARTICLE",
        publishing_channel="WEB",
        current_status=status,
    )
    db.add(sub)
    db.flush()
    # version
    ver = ContentVersion(
        organisation_id=org.id,
        submission_id=sub.id,
        version_number=1,
        content_text="Hello",
        content_hash="abc",
        created_by=user.id,
    )
    db.add(ver)
    db.flush()
    return sub, ver


def test_dashboard_endpoint_success(client: TestClient, test_data, db_session: Session):
    org = test_data["org1"]
    admin = test_data["admin_user"]
    make_submission(db_session, org, admin, title="Item 1", status="SUBMITTED")
    db_session.commit()

    token = test_data["admin_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Organisation-Id": org.id}
    resp = client.get("/api/v1/governance/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "total_submissions" in data["data"]
    assert data["data"]["total_submissions"] >= 1


def test_submissions_pagination_and_filtering(client: TestClient, test_data, db_session: Session):
    org = test_data["org1"]
    admin = test_data["admin_user"]
    for i in range(25):
        make_submission(db_session, org, admin, title=f"Item {i}", status="SUBMITTED" if i % 2 == 0 else "DRAFT")
    db_session.commit()

    token = test_data["admin_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Organisation-Id": org.id}
    resp = client.get("/api/v1/governance/submissions?page=2&page_size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 25
    assert data["page"] == 2
    assert len(data["items"]) == 10

    resp = client.get("/api/v1/governance/submissions?status=DRAFT", headers=headers)
    assert resp.status_code == 200
    assert all(item["current_status"] == "DRAFT" for item in resp.json()["items"])

    resp = client.get("/api/v1/governance/submissions?search=Item%2019", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert "Item 19" in items[0]["title"]


def test_create_submission_with_automated_checks(client: TestClient, test_data, db_session: Session):
    org = test_data["org1"]
    token = test_data["creator_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Organisation-Id": org.id}

    # Add a terminology rule first
    rule = TerminologyRule(
        organisation_id=org.id,
        prohibited_term="cheap",
        preferred_term="cost-effective",
        category="PRICING",
        match_type=TerminologyMatchType.EXACT.value,
        severity=TerminologySeverity.HIGH.value,
        status="ACTIVE",
    )
    db_session.add(rule)
    db_session.commit()

    payload = {
        "title": "Spring Product Launch",
        "content_type": "BLOG_POST",
        "publishing_channel": "WEB",
        "content_text": "Our new cloud software is very cheap and reliable for all startups.",
    }
    resp = client.post("/api/v1/governance/submissions", json=payload, headers=headers)
    assert resp.status_code == 201
    res_data = resp.json()
    assert res_data["success"] is True
    sub = res_data["data"]
    assert sub["title"] == "Spring Product Launch"
    assert sub["current_version_number"] == 1
    assert len(sub["versions"]) == 1

    # Check that finding was automatically detected
    assert sub["latest_review_result"] is not None
    findings = sub["latest_review_result"]["findings"]
    assert len(findings) == 1
    assert findings[0]["original_text"] == "cheap"
    assert findings[0]["suggestion"]["suggested_text"] == "cost-effective"

    # Test applying suggestion
    sugg_id = findings[0]["suggestion"]["id"]
    sugg_resp = client.post(
        f"/api/v1/governance/suggestions/{sugg_id}/action",
        json={"action": "APPLY"},
        headers=headers,
    )
    assert sugg_resp.status_code == 200
    assert sugg_resp.json()["data"]["status"] == "APPLIED"

    # Fetch submission detail and verify version was incremented to 2 with replaced text
    detail_resp = client.get(f"/api/v1/governance/submissions/{sub['id']}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["current_version_number"] == 2
    assert len(detail["versions"]) == 2
    assert "cost-effective" in detail["versions"][0]["content_text"]
    assert "cheap" not in detail["versions"][0]["content_text"]


def test_review_decision_workflow(client: TestClient, test_data, db_session: Session):
    org = test_data["org1"]
    admin = test_data["admin_user"]
    sub, ver = make_submission(db_session, org, admin, title="Policy Brief")
    db_session.commit()

    rev_token = test_data["reviewer_token"]
    headers = {"Authorization": f"Bearer {rev_token}", "X-Organisation-Id": org.id}

    # Reviewer approves submission
    resp = client.post(
        f"/api/v1/governance/submissions/{sub.id}/decide",
        json={"decision": "APPROVED", "notes": "Meets all compliance criteria."},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["current_status"] == "APPROVED"


def test_analytics_overview_endpoint(client: TestClient, test_data, db_session: Session):
    org = test_data["org1"]
    token = test_data["admin_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Organisation-Id": org.id}

    resp = client.get("/api/v1/analytics/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    overview = data["data"]
    assert "compliance_rate" in overview
    assert "total_submissions_analyzed" in overview
    assert "top_violated_rules" in overview
    assert "violations_by_channel" in overview
    assert "violations_by_severity" in overview


def test_evidence_endpoint_success(client: TestClient, test_data, db_session: Session):
    org = test_data["org1"]
    admin = test_data["admin_user"]
    sub, ver = make_submission(db_session, org, admin)

    rr = ReviewResult(
        organisation_id=org.id,
        review_job_id="job-123",
        submission_id=sub.id,
        content_version_id=ver.id,
        overall_status="COMPLETED"
    )
    db_session.add(rr)
    db_session.flush()

    finding = Finding(
        organisation_id=org.id,
        review_result_id=rr.id,
        category="CLAIM",
        status=FindingStatus.DETECTED.value,
        severity=SeverityLevel.HIGH.value,
        confidence_level="HIGH",
        original_text="test",
        start_offset=0,
        end_offset=4,
    )
    db_session.add(finding)
    db_session.flush()

    evidence = FindingEvidence(
        organisation_id=org.id,
        finding_id=finding.id,
        document_id="doc1",
        document_version_id="v1",
        chunk_id="c1",
        source_quote="quote",
        verification_status="VERIFIED",
    )
    db_session.add(evidence)
    db_session.commit()

    token = test_data["admin_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Organisation-Id": org.id}
    resp = client.get(f"/api/v1/governance/evidence/{evidence.id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == evidence.id
    assert data["finding_id"] == finding.id


def test_evidence_cross_tenant_forbidden(client: TestClient, test_data, db_session: Session):
    org1 = test_data["org1"]
    org2 = test_data["org2"]
    admin1 = test_data["admin_user"]
    sub, ver = make_submission(db_session, org1, admin1)

    rr = ReviewResult(
        organisation_id=org1.id,
        review_job_id="job-456",
        submission_id=sub.id,
        content_version_id=ver.id,
        overall_status="COMPLETED"
    )
    db_session.add(rr)
    db_session.flush()

    finding = Finding(
        organisation_id=org1.id,
        review_result_id=rr.id,
        category="CLAIM",
        status=FindingStatus.DETECTED.value,
        severity=SeverityLevel.HIGH.value,
        confidence_level="HIGH",
        original_text="test",
        start_offset=0,
        end_offset=4,
    )
    db_session.add(finding)
    db_session.flush()

    evidence = FindingEvidence(
        organisation_id=org1.id,
        finding_id=finding.id,
        document_id="doc1",
        document_version_id="v1",
        chunk_id="c1",
        source_quote="quote",
        verification_status="VERIFIED",
    )
    db_session.add(evidence)
    db_session.commit()

    token = test_data["org2_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Organisation-Id": org2.id}
    resp = client.get(f"/api/v1/governance/evidence/{evidence.id}", headers=headers)
    assert resp.status_code == 404
