def test_list_members_paginated(client, test_data):
    """Admin can list members with pagination."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    response = client.get("/api/v1/members?page=1&page_size=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] >= 4
    assert len(data["data"]["items"]) >= 4


def test_admin_invites_new_member(client, test_data):
    """Admin can invite a new user with assigned role."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    payload = {
        "email": "new.member@novatech.io",
        "full_name": "New Team Member",
        "role": "BRAND_MANAGER"
    }
    response = client.post("/api/v1/members", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "new.member@novatech.io"
    assert data["data"]["role"] == "BRAND_MANAGER"


def test_invite_existing_member_fails_conflict(client, test_data):
    """Attempting to add an already-existing member to the same workspace returns 409."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    payload = {
        "email": "creator@test.io",
        "full_name": "Existing Creator",
        "role": "CREATOR"
    }
    response = client.post("/api/v1/members", json=payload, headers=headers)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESOURCE_CONFLICT"


def test_admin_updates_member_role(client, test_data):
    """Admin can update an existing member's role."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    # List members to find creator membership id
    list_res = client.get("/api/v1/members", headers=headers)
    creator_member = next(m for m in list_res.json()["data"]["items"] if m["email"] == "creator@test.io")

    payload = {"role": "REVIEWER"}
    patch_res = client.patch(f"/api/v1/members/{creator_member['id']}/role", json=payload, headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["role"] == "REVIEWER"


def test_admin_removes_member(client, test_data):
    """Admin can remove a non-admin member from the workspace."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    # First add a member to remove
    add_res = client.post("/api/v1/members", json={
        "email": "temporary.contractor@test.io",
        "full_name": "Temporary Contractor",
        "role": "CREATOR"
    }, headers=headers)
    member_id = add_res.json()["data"]["id"]

    del_res = client.delete(f"/api/v1/members/{member_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Confirm member no longer in roster
    list_res = client.get("/api/v1/members", headers=headers)
    emails = [m["email"] for m in list_res.json()["data"]["items"]]
    assert "temporary.contractor@test.io" not in emails

