def test_creator_cannot_update_workspace_settings(client, test_data):
    """Content Creators cannot modify workspace governance settings (receives 403)."""
    headers = {
        "Authorization": f"Bearer {test_data['creator_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    payload = {"strict_mode": True}
    response = client.patch("/api/v1/organisations/current/settings", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PERMISSION_DENIED"


def test_creator_cannot_update_workspace_profile(client, test_data):
    """Content Creators cannot change organization profile details (receives 403)."""
    headers = {
        "Authorization": f"Bearer {test_data['creator_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    payload = {"name": "Hacked Name"}
    response = client.patch("/api/v1/organisations/current", json=payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_reviewer_cannot_invite_members(client, test_data):
    """Reviewers cannot invite or add members (receives 403)."""
    headers = {
        "Authorization": f"Bearer {test_data['reviewer_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    payload = {
        "email": "intruder@test.io",
        "full_name": "Intruder User",
        "role": "CREATOR"
    }
    response = client.post("/api/v1/members", json=payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_non_admin_cannot_change_member_roles(client, test_data):
    """Non-admin (Brand Manager or Creator) cannot change member roles (receives 403)."""
    headers_creator = {
        "Authorization": f"Bearer {test_data['creator_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    response = client.patch(f"/api/v1/members/some-id/role", json={"role": "ADMIN"}, headers=headers_creator)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_non_admin_cannot_remove_members(client, test_data):
    """Non-admin cannot remove members from workspace (receives 403)."""
    headers_reviewer = {
        "Authorization": f"Bearer {test_data['reviewer_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    response = client.delete(f"/api/v1/members/some-id", headers=headers_reviewer)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_cannot_demote_sole_remaining_admin(client, test_data):
    """System must prevent demoting the sole remaining Workspace Admin."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    list_res = client.get("/api/v1/members", headers=headers)
    members = list_res.json()["data"]["items"]
    admin_member = next(m for m in members if m["role"] == "ADMIN")

    demote_payload = {"role": "CREATOR"}
    response = client.patch(f"/api/v1/members/{admin_member['id']}/role", json=demote_payload, headers=headers)
    assert response.status_code == 422
    assert "Cannot demote the only remaining Workspace Admin" in response.json()["error"]["message"]


def test_cannot_remove_sole_remaining_admin(client, test_data):
    """System must prevent removing the sole remaining Workspace Admin."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    list_res = client.get("/api/v1/members", headers=headers)
    members = list_res.json()["data"]["items"]
    admin_member = next(m for m in members if m["role"] == "ADMIN")

    response = client.delete(f"/api/v1/members/{admin_member['id']}", headers=headers)
    assert response.status_code == 422
    assert "Cannot remove the only remaining Workspace Admin" in response.json()["error"]["message"]
