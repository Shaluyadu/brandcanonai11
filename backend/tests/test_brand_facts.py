"""
Automated tests for Approved Facts & Claims lifecycle and permissions.
"""
import pytest


def test_fact_creation_and_approval_workflow(client, test_data):
    """Creator can submit a fact; Brand Manager or Admin approves/rejects it."""
    creator_headers = {
        "Authorization": f"Bearer {test_data['creator_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }
    manager_headers = {
        "Authorization": f"Bearer {test_data['manager_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    # 1. Creator creates a fact
    payload = {
        "title": "SOC-2 Type II Certified",
        "claim_text": "BrandCanon AI is fully SOC-2 Type II certified with annual third-party audits.",
        "category": "COMPLIANCE",
        "evidence_quote": "Audited by Ernst & Young on October 2026.",
        "applicable_region": "GLOBAL",
        "applicable_audience": "ENTERPRISE"
    }
    res = client.post("/api/v1/brand/facts", headers=creator_headers, json=payload)
    assert res.status_code == 201
    fact = res.json()["data"]
    assert fact["title"] == "SOC-2 Type II Certified"
    assert fact["status"] == "PENDING_APPROVAL"
    fact_id = fact["id"]

    # 2. Creator CANNOT approve their own or any fact
    unauth_approve = client.post(
        f"/api/v1/brand/facts/{fact_id}/approve",
        headers=creator_headers,
        json={"decision": "APPROVED"}
    )
    assert unauth_approve.status_code == 403

    # 3. Manager approves the fact
    approve_res = client.post(
        f"/api/v1/brand/facts/{fact_id}/approve",
        headers=manager_headers,
        json={"decision": "APPROVED", "reason": "Verified audit report"}
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["status"] == "APPROVED"
    assert approve_res.json()["data"]["approved_by"] is not None

    # 4. Filter by status returns approved fact
    list_res = client.get("/api/v1/brand/facts?status=APPROVED", headers=creator_headers)
    assert list_res.status_code == 200
    items = list_res.json()["data"]["items"]
    assert any(f["id"] == fact_id for f in items)


def test_fact_rejection_and_archival(client, test_data):
    """Brand Manager can reject or archive facts."""
    manager_headers = {
        "Authorization": f"Bearer {test_data['manager_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    payload = {
        "title": "100% Free Forever",
        "claim_text": "All features are completely free forever.",
        "category": "PRICING"
    }
    res = client.post("/api/v1/brand/facts", headers=manager_headers, json=payload)
    assert res.status_code == 201
    fact_id = res.json()["data"]["id"]

    # Reject
    reject_res = client.post(
        f"/api/v1/brand/facts/{fact_id}/reject",
        headers=manager_headers,
        json={"decision": "REJECTED", "reason": "Incorrect pricing claim"}
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["data"]["status"] == "REJECTED"

    # Archive
    archive_res = client.post(
        f"/api/v1/brand/facts/{fact_id}/archive",
        headers=manager_headers,
        json={"decision": "ARCHIVED", "reason": "Archived"}
    )
    assert archive_res.status_code == 200
    assert archive_res.json()["data"]["status"] == "ARCHIVED"


def test_cross_tenant_facts_isolation(client, test_data):
    """Org 2 user cannot access or modify Org 1's facts."""
    org1_headers = {
        "Authorization": f"Bearer {test_data['manager_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }
    org2_headers = {
        "Authorization": f"Bearer {test_data['org2_token']}",
        "X-Organisation-Id": test_data["org2"].id,
    }

    # Org 1 creates fact
    payload = {
        "title": "NovaTech Proprietary Tech",
        "claim_text": "Proprietary AI algorithms patented in 2026.",
        "category": "INTELLECTUAL_PROPERTY"
    }
    res = client.post("/api/v1/brand/facts", headers=org1_headers, json=payload)
    assert res.status_code == 201
    fact_id = res.json()["data"]["id"]

    # Org 2 attempts to get Org 1's fact
    res_get = client.get(f"/api/v1/brand/facts/{fact_id}", headers=org2_headers)
    assert res_get.status_code == 404

    # Org 2 attempts to modify Org 1's fact
    res_patch = client.patch(
        f"/api/v1/brand/facts/{fact_id}",
        headers=org2_headers,
        json={"title": "Hacked Title"}
    )
    assert res_patch.status_code == 404

