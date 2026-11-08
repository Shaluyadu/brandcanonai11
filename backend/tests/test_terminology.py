"""
Automated tests for Terminology rules and the deterministic matching engine.
"""
import pytest
from app.ingestion.terminology_engine import TerminologyMatcher
from app.models.brand_knowledge import TerminologyRule


def test_deterministic_matcher_whole_word():
    """Verify WHOLE_WORD match does not trigger false positives on substrings."""
    rule = TerminologyRule(
        id="rule-1",
        organisation_id="org-1",
        prohibited_term="cheap",
        preferred_term="affordable",
        match_type="WHOLE_WORD",
        case_sensitive=False,
        severity="HIGH",
        category="PRICING",
        status="ACTIVE"
    )
    matcher = TerminologyMatcher(rules=[rule])

    # Should NOT match substring in "cheapskate"
    matches_sub = matcher.match_text("He is a cheapskate person.")
    assert len(matches_sub) == 0

    # Should match standalone word "cheap"
    matches = matcher.match_text("Our products are very cheap compared to competitors.")
    assert len(matches) == 1
    assert matches[0].matched_text.lower() == "cheap"
    assert matches[0].preferred_term == "affordable"


def test_deterministic_matcher_phrase():
    """Verify multi-word phrase matching with flexible whitespace."""
    rule = TerminologyRule(
        id="rule-2",
        organisation_id="org-1",
        prohibited_term="artificial intelligence robot",
        preferred_term="AI assistant",
        match_type="PHRASE",
        case_sensitive=False,
        severity="MEDIUM",
        category="TECHNOLOGY",
        status="ACTIVE"
    )
    matcher = TerminologyMatcher(rules=[rule])

    text = "Meet our new artificial   intelligence   robot for customer support."
    matches = matcher.match_text(text)
    assert len(matches) == 1
    assert matches[0].preferred_term == "AI assistant"


def test_deterministic_matcher_case_sensitivity():
    """Verify case sensitivity flag."""
    rule_sensitive = TerminologyRule(
        id="rule-3",
        organisation_id="org-1",
        prohibited_term="brandcanon",
        preferred_term="BrandCanon AI",
        match_type="EXACT",
        case_sensitive=True,
        severity="LOW",
        category="BRANDING",
        status="ACTIVE"
    )
    matcher = TerminologyMatcher(rules=[rule_sensitive])

    # Mismatched case should NOT match
    assert len(matcher.match_text("Welcome to BrandCanon today.")) == 0

    # Exact lowercase matches
    matches = matcher.match_text("Welcome to brandcanon today.")
    assert len(matches) == 1


def test_terminology_api_crud_and_check(client, test_data):
    """End-to-end terminology rule creation, retrieval, and interactive checking."""
    headers = {
        "Authorization": f"Bearer {test_data['manager_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    # 1. Create rule
    payload = {
        "prohibited_term": "synergy",
        "preferred_term": "collaboration",
        "match_type": "WHOLE_WORD",
        "case_sensitive": False,
        "severity": "HIGH",
        "category": "COMMUNICATION",
        "description": "Avoid corporate buzzwords"
    }
    res = client.post("/api/v1/brand/terminology", headers=headers, json=payload)
    assert res.status_code == 201
    rule = res.json()["data"]
    assert rule["prohibited_term"] == "synergy"
    assert rule["status"] == "ACTIVE"
    rule_id = rule["id"]

    # 2. Interactive text check endpoint
    check_res = client.post(
        "/api/v1/brand/terminology/check",
        headers=headers,
        json={"text": "We need cross-functional synergy to deliver on Q4 goals."}
    )
    assert check_res.status_code == 200
    check_data = check_res.json()["data"]
    assert len(check_data) == 1
    assert check_data[0]["matched_text"].lower() == "synergy"
    assert check_data[0]["preferred_term"] == "collaboration"

    # 3. Creator can check text but cannot create rule
    creator_headers = {
        "Authorization": f"Bearer {test_data['creator_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }
    creator_check = client.post(
        "/api/v1/brand/terminology/check",
        headers=creator_headers,
        json={"text": "Let us achieve synergy together."}
    )
    assert creator_check.status_code == 200
    assert len(creator_check.json()["data"]) == 1

    creator_forbidden = client.post(
        "/api/v1/brand/terminology",
        headers=creator_headers,
        json=payload
    )
    assert creator_forbidden.status_code == 403


def test_cross_tenant_terminology_isolation(client, test_data):
    """Rules created in Org 1 do not match text or appear in Org 2."""
    org1_headers = {
        "Authorization": f"Bearer {test_data['manager_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }
    org2_headers = {
        "Authorization": f"Bearer {test_data['org2_token']}",
        "X-Organisation-Id": test_data["org2"].id,
    }

    # Org 1 rule
    payload = {
        "prohibited_term": "ultra-fast",
        "preferred_term": "high-performance",
        "match_type": "WHOLE_WORD",
        "case_sensitive": False
    }
    res = client.post("/api/v1/brand/terminology", headers=org1_headers, json=payload)
    assert res.status_code == 201

    # Check text in Org 2: Should NOT match Org 1's rule
    check_res = client.post(
        "/api/v1/brand/terminology/check",
        headers=org2_headers,
        json={"text": "Our new engine is ultra-fast and reliable."}
    )
    assert check_res.status_code == 200
    assert len(check_res.json()["data"]) == 0

