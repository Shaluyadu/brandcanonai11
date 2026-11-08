def test_get_current_organisation(client, test_data):
    """User can access their active workspace details and settings."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    response = client.get("/api/v1/organisations/current", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == test_data["org1"].id
    assert data["data"]["name"] == "NovaTech"
    assert data["data"]["settings"] is not None
    assert data["data"]["settings"]["enforce_brand_voice"] is True


def test_update_current_organisation_as_admin(client, test_data):
    """Admin can update workspace metadata."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    payload = {
        "name": "NovaTech Global",
        "industry": "Enterprise AI Governance"
    }
    response = client.patch("/api/v1/organisations/current", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "NovaTech Global"
    assert data["data"]["industry"] == "Enterprise AI Governance"


def test_update_settings_as_admin(client, test_data):
    """Admin can update governance enforcement settings."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    payload = {
        "enforce_brand_voice": True,
        "strict_mode": True
    }
    response = client.patch("/api/v1/organisations/current/settings", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["strict_mode"] is True


def test_create_new_organisation_workspace(client, test_data):
    """Authenticated user can create a second workspace and becomes ADMIN."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}"
    }
    payload = {
        "name": "BrandCanon EMEA",
        "industry": "Regional Marketing",
        "domain": "emea.novatech.io"
    }
    response = client.post("/api/v1/organisations", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "BrandCanon EMEA"
    assert data["data"]["slug"] == "brandcanon-emea"
