import pytest
from app.models.progress import CourseProgress

def test_get_academies_roadmap_order(client):
    # Register & Login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "roadmap@example.com",
            "name": "Roadmap User",
            "password": "Password123!",
        },
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "username": "roadmap@example.com",
            "password": "Password123!",
        },
    )
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Fetch academies list
    resp = client.get("/api/v1/labs/academies/list", headers=headers)
    assert resp.status_code == 200
    academies = resp.json()
    
    # Assert sequence follows the requested Roadmap Order
    expected_order = [
        "linux",
        "git",
        "docker",
        "cicd",
        "github-actions",
        "jenkins",
        "ansible",
        "terraform",
        "aws",
        "azure",
        "kubernetes",
        "monitoring",
        "observability"
    ]
    actual_order = [a["id"] for a in academies]
    # Check that the first few follow our roadmap exactly
    for expected, actual in zip(expected_order, actual_order):
        assert expected == actual


def test_certificates_and_achievements(client, db):
    # Register & Login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "certs@example.com",
            "name": "Certs User",
            "password": "Password123!",
        },
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "username": "certs@example.com",
            "password": "Password123!",
        },
    )
    user_id = login_resp.json().get("user_id")
    access_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Verify initially no certificates
    certs_resp = client.get("/api/v1/labs/certificates/list", headers=headers)
    assert certs_resp.status_code == 200
    assert len(certs_resp.json()) == 0

    # Retrieve user from DB to inject 100% course progress
    from app.models.user import User as UserModel
    user_db = db.query(UserModel).filter(UserModel.email == "certs@example.com").first()
    assert user_db is not None

    # Inject completed CourseProgress for 'git-fundamentals'
    progress = CourseProgress(
        user_id=user_db.id,
        course_slug="git-fundamentals",
        percentage=100,
        completed_lessons=[1, 2, 3, 4]
    )
    db.add(progress)
    db.commit()

    # Query certificates again
    certs_resp = client.get("/api/v1/labs/certificates/list", headers=headers)
    assert certs_resp.status_code == 200
    certs = certs_resp.json()
    assert len(certs) == 1
    assert certs[0]["target_id"] == "git-fundamentals"
    assert certs[0]["type"] == "course"

    # Query achievements
    ach_resp = client.get("/api/v1/labs/achievements/list", headers=headers)
    assert ach_resp.status_code == 200
    ach_data = ach_resp.json()
    assert "streak" in ach_data
    assert "badges" in ach_data
    
    # Assert path progress is tracked
    path_badge = next((b for b in ach_data["badges"] if b["target_id"] == "devops-beginner"), None)
    assert path_badge is not None
    # git-fundamentals is part of DevOps Beginner path
    assert path_badge["completed_count"] > 0
