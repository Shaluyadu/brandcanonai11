def test_list_audit_logs_as_admin(client, test_data):
    """Admin can list and paginate audit log events for the active workspace."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    response = client.get("/api/v1/audit?page=1&page_size=20", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert data["data"]["total"] >= 1


def test_list_audit_logs_as_brand_manager(client, test_data):
    """Brand Manager can also view audit history."""
    headers = {
        "Authorization": f"Bearer {test_data['manager_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    response = client.get("/api/v1/audit", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_creator_cannot_view_audit_logs(client, test_data):
    """Content Creator cannot access organisation audit logs (receives 403)."""
    headers = {
        "Authorization": f"Bearer {test_data['creator_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    response = client.get("/api/v1/audit", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_audit_logs_record_member_role_changes(client, test_data):
    """Role modification generates an immutable audit record."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    # List members
    list_res = client.get("/api/v1/members", headers=headers)
    creator_member = next(m for m in list_res.json()["data"]["items"] if m["email"] == "creator@test.io")

    # Update role
    client.patch(f"/api/v1/members/{creator_member['id']}/role", json={"role": "REVIEWER"}, headers=headers)

    # Check audit log for MEMBER_ROLE_UPDATED
    audit_res = client.get("/api/v1/audit?event_type=MEMBER_ROLE_UPDATED", headers=headers)
    assert audit_res.status_code == 200
    events = audit_res.json()["data"]["items"]
    assert len(events) >= 1
    latest = events[0]
    assert latest["event_type"] == "MEMBER_ROLE_UPDATED"
    assert latest["entity_type"] == "MEMBERSHIP"
    assert latest["metadata_json"]["new_role"] == "REVIEWER"

