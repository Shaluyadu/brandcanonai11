def test_user_cannot_access_foreign_tenant(client, test_data):
    """
    User belonging only to Org 1 attempts to pass X-Organisation-Id of Org 2.
    Must be strictly blocked with 403 TENANT_ACCESS_FORBIDDEN.
    """
    foreign_headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org2"].id
    }
    response = client.get("/api/v1/organisations/current", headers=foreign_headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TENANT_ACCESS_FORBIDDEN"


def test_members_list_isolated_between_tenants(client, test_data):
    """
    Member query for Org 1 must only return Org 1 members and strictly zero Org 2 members.
    """
    headers_org1 = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    res_org1 = client.get("/api/v1/members", headers=headers_org1)
    assert res_org1.status_code == 200
    emails_org1 = [m["email"] for m in res_org1.json()["data"]["items"]]

    assert "admin@test.io" in emails_org1
    assert "creator@test.io" in emails_org1
    assert "reviewer@test.io" in emails_org1
    assert "acme_user@acme.com" not in emails_org1  # MUST NEVER LEAK ORG 2 USER

    headers_org2 = {
        "Authorization": f"Bearer {test_data['org2_token']}",
        "X-Organisation-Id": test_data["org2"].id
    }
    res_org2 = client.get("/api/v1/members", headers=headers_org2)
    assert res_org2.status_code == 200
    emails_org2 = [m["email"] for m in res_org2.json()["data"]["items"]]

    assert "acme_user@acme.com" in emails_org2
    assert "admin@test.io" not in emails_org2  # MUST NEVER LEAK ORG 1 USER


def test_audit_logs_isolated_between_tenants(client, test_data):
    """
    Audit log queries are strictly scoped to the active organization.
    """
    headers_org1 = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    res_org1 = client.get("/api/v1/audit", headers=headers_org1)
    assert res_org1.status_code == 200
    items_org1 = res_org1.json()["data"]["items"]
    for item in items_org1:
        assert item["organisation_id"] == test_data["org1"].id

    headers_org2 = {
        "Authorization": f"Bearer {test_data['org2_token']}",
        "X-Organisation-Id": test_data["org2"].id
    }
    res_org2 = client.get("/api/v1/audit", headers=headers_org2)
    assert res_org2.status_code == 200
    items_org2 = res_org2.json()["data"]["items"]
    for item in items_org2:
        assert item["organisation_id"] == test_data["org2"].id
