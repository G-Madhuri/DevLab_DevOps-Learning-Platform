import pytest


def test_get_me_unauthorized(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_get_me_authorized(client):
    # Register & Login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "name": "Me User",
            "password": "Password123!",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "me@example.com",
            "password": "Password123!",
        },
    )
    access_token = login_response.json()["access_token"]

    # Access /users/me
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["name"] == "Me User"


def test_update_me_profile_name(client):
    # Register & Login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "update@example.com",
            "name": "Old Name",
            "password": "Password123!",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "update@example.com",
            "password": "Password123!",
        },
    )
    access_token = login_response.json()["access_token"]

    # Update name
    response = client.put(
        "/api/v1/users/me",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_update_me_password_rotation(client):
    # Register & Login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "password@example.com",
            "name": "Password User",
            "password": "Password123!",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "password@example.com",
            "password": "Password123!",
        },
    )
    access_token = login_response.json()["access_token"]

    # Update password successfully
    response = client.put(
        "/api/v1/users/me",
        json={
            "current_password": "Password123!",
            "new_password": "NewPassword123!",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200

    # Try to login with old password (should fail)
    fail_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "password@example.com",
            "password": "Password123!",
        },
    )
    assert fail_response.status_code == 401

    # Try to login with new password (should succeed)
    success_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "password@example.com",
            "password": "NewPassword123!",
        },
    )
    assert success_response.status_code == 200
