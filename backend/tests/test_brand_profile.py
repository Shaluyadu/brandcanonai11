"""
Automated tests for Brand Profile and Brand Knowledge Overview stats.
"""
import pytest


def test_brand_profile_crud_and_overview(client, test_data):
    """Admin creates brand profile, updates it, and checks overview metrics."""
    admin_headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }
    creator_headers = {
        "Authorization": f"Bearer {test_data['creator_token']}",
        "X-Organisation-Id": test_data["org1"].id,
    }

    # 1. Initially profile is None
    get_res = client.get("/api/v1/brand/profile", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"] is None

    # 2. Creator cannot create brand profile
    payload = {
        "brand_name": "NovaTech Cloud",
        "industry": "Enterprise Software",
        "domain": "novatech.io",
        "description": "Enterprise cloud compliance and brand governance.",
        "brand_voice": "Authoritative, objective, transparent, and precise.",
        "target_audience": "Enterprise Compliance Officers and CMOs",
        "publishing_channels": ["Website", "LinkedIn", "Press Releases"],
        "applicable_regions": ["North America", "Europe"]
    }
    unauth = client.post("/api/v1/brand/profile", headers=creator_headers, json=payload)
    assert unauth.status_code == 403

    # 3. Admin creates brand profile
    create_res = client.post("/api/v1/brand/profile", headers=admin_headers, json=payload)
    assert create_res.status_code == 201
    profile = create_res.json()["data"]
    assert profile["brand_name"] == "NovaTech Cloud"
    assert "Website" in profile["publishing_channels"]

    # 4. Patch profile
    patch_res = client.patch(
        "/api/v1/brand/profile",
        headers=admin_headers,
        json={"brand_name": "NovaTech Enterprise AI"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["brand_name"] == "NovaTech Enterprise AI"

    # 5. Check Overview stats
    overview_res = client.get("/api/v1/brand/overview", headers=admin_headers)
    assert overview_res.status_code == 200
    stats = overview_res.json()["data"]
    assert "total_documents" in stats
    assert "total_facts" in stats
    assert "total_terminology_rules" in stats
    assert "total_chunks" in stats

