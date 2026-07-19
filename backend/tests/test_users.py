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


def test_user_daily_streak_calculation(db):
    """
    Verifies daily streak calculation logic using LabSessions and CourseProgress updates.
    """
    from datetime import datetime, timedelta, timezone
    from app.models.user import User
    from app.models.session import LabSession
    from app.models.progress import CourseProgress
    from app.services.user import user_service

    # Create dummy user
    user = User(
        name="Streak Tester",
        email="streak@example.com",
        password_hash="hashed_pw"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 1. No activity: default streak should be 1
    assert user_service.calculate_streak(db, user.id) == 1

    # 2. Activity today
    s1 = LabSession(
        user_id=user.id,
        lab_name="linux-basics",
        status="running",
        created_at=datetime.now(timezone.utc)
    )
    db.add(s1)
    db.commit()

    assert user_service.calculate_streak(db, user.id) == 1

    # 3. Activity yesterday (using UTC offset that maps to yesterday local)
    s2 = LabSession(
        user_id=user.id,
        lab_name="docker-basics",
        status="stopped",
        created_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    db.add(s2)
    db.commit()

    assert user_service.calculate_streak(db, user.id) == 2

    # 4. Activity via CourseProgress 2 days ago
    p1 = CourseProgress(
        user_id=user.id,
        course_slug="linux-basics",
        completed_lessons=["intro"],
        updated_at=datetime.now(timezone.utc) - timedelta(days=2)
    )
    db.add(p1)
    db.commit()

    assert user_service.calculate_streak(db, user.id) == 3

    # Clean up
    db.delete(s1)
    db.delete(s2)
    db.delete(p1)
    db.delete(user)
    db.commit()

