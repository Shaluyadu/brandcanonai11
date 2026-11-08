def test_register_creates_user_and_admin_workspace(client):
    """Verify new user registration creates user, org workspace, and ADMIN membership."""
    payload = {
        "email": "sarah.connor@cyberdyne.io",
        "password": "SecurePassword123!",
        "full_name": "Sarah Connor",
        "organisation_name": "Cyberdyne Systems"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["access_token"].startswith("bcs_")  # Opaque session token
    assert data["data"]["user"]["email"] == "sarah.connor@cyberdyne.io"
    assert data["data"]["user"]["is_verified"] is False  # Verification unconfirmed
    assert data["data"]["active_organisation"]["name"] == "Cyberdyne Systems"
    assert data["data"]["current_role"] == "ADMIN"


def test_register_duplicate_email_fails(client, test_data):
    """Duplicate email registration is rejected with HTTP 409 conflict."""
    payload = {
        "email": "admin@test.io",
        "password": "AnotherPassword123!",
        "full_name": "Duplicate User",
        "organisation_name": "Duplicate Org"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_CONFLICT"


def test_login_success_and_sets_cookie(client, test_data):
    """User can log in with verified Argon2id credentials and receive session cookie & token."""
    payload = {
        "email": "admin@test.io",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["email"] == "admin@test.io"
    assert data["data"]["current_role"] == "ADMIN"
    # Verify HttpOnly cookie header was set
    assert "brandcanon_session" in response.headers.get("set-cookie", "")


def test_login_invalid_password_fails(client, test_data):
    """Invalid password fails with HTTP 401."""
    payload = {
        "email": "admin@test.io",
        "password": "WrongPassword!"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"


def test_get_me_profile(client, test_data):
    """Authenticated user can retrieve /auth/me profile with active workspace and permitted orgs."""
    headers = {
        "Authorization": f"Bearer {test_data['admin_token']}",
        "X-Organisation-Id": test_data["org1"].id
    }
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "admin@test.io"
    assert data["data"]["current_role"] == "ADMIN"
    assert data["data"]["active_organisation"]["id"] == test_data["org1"].id
    assert len(data["data"]["permitted_organisations"]) >= 1


def test_logout_revokes_session(client, test_data):
    """Logout endpoint revokes session in database and clears cookies."""
    # First login to get a fresh token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "creator@test.io",
        "password": "Password123!"
    })
    token = login_res.json()["data"]["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organisation-Id": test_data["org1"].id
    }

    # Verify token works
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200

    # Logout
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Subsequent request using the revoked token MUST fail with 401
    blocked_res = client.get("/api/v1/auth/me", headers=headers)
    assert blocked_res.status_code == 401
    assert blocked_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"
