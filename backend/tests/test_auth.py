import pytest


def test_register_user_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "name": "Test User",
            "password": "Password123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data


def test_register_user_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test2@example.com",
            "name": "Test User",
            "password": "weak",
        },
    )
    assert response.status_code == 422


def test_register_user_duplicate_email(client):
    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "name": "First User",
            "password": "Password123!",
        },
    )
    # Register second user with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "name": "Second User",
            "password": "Password123!",
        },
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_success(client):
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "name": "Login User",
            "password": "Password123!",
        },
    )
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "login@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login@example.com"


def test_login_incorrect_credentials(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_refresh_token_success(client):
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "name": "Refresh User",
            "password": "Password123!",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "refresh@example.com",
            "password": "Password123!",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout_success(client):
    # Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout@example.com",
            "name": "Logout User",
            "password": "Password123!",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "logout@example.com",
            "password": "Password123!",
        },
    )
    refresh_token = login_response.json()["refresh_token"]

    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully logged out"

    # Try to refresh with revoked token
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401
