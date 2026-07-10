import pytest
import os
from app.models.session import LabSession


def get_auth_headers(client, email="session@example.com", name="Session User"):
    """
    Helper to register a user, login, and obtain authorization headers.
    """
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": name,
            "password": "Password123!",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": email,
            "password": "Password123!",
        },
    )
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_launch_lab_success(client):
    headers = get_auth_headers(client, "launch@example.com")
    response = client.post("/api/v1/labs/linux/launch", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["lab_name"] == "linux-basics"
    assert data["status"] == "running"
    assert "id" in data
    assert "container_id" in data


def test_launch_lab_double_launch(client):
    headers = get_auth_headers(client, "double@example.com")
    # Launch first session
    r1 = client.post("/api/v1/labs/linux/launch", headers=headers)
    assert r1.status_code == 200
    id1 = r1.json()["id"]

    # Launch again — should return existing running session
    r2 = client.post("/api/v1/labs/linux/launch", headers=headers)
    assert r2.status_code == 200
    id2 = r2.json()["id"]
    assert id1 == id2


def test_get_active_session(client):
    headers = get_auth_headers(client, "active_s@example.com")
    # Before launch — active is null
    r1 = client.get("/api/v1/labs/linux/active", headers=headers)
    assert r1.status_code == 200
    assert r1.json() is None

    # Launch
    client.post("/api/v1/labs/linux/launch", headers=headers)

    # After launch — returns active session
    r2 = client.get("/api/v1/labs/linux/active", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["lab_name"] == "linux-basics"


def test_stop_lab_success(client):
    headers = get_auth_headers(client, "stop@example.com")
    # Launch
    launch_res = client.post("/api/v1/labs/linux/launch", headers=headers)
    session_id = launch_res.json()["id"]

    # Stop session
    response = client.post(f"/api/v1/labs/linux/{session_id}/stop", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "stopped"

    # Confirm active is now null
    active_res = client.get("/api/v1/labs/linux/active", headers=headers)
    assert active_res.status_code == 200
    assert active_res.json() is None


def test_get_sessions_list(client):
    headers = get_auth_headers(client, "list@example.com")
    client.post("/api/v1/labs/linux/launch", headers=headers)
    
    response = client.get("/api/v1/labs/linux/sessions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["sessions"]) >= 1


def test_validate_task_fail_and_success(client):
    headers = get_auth_headers(client, "validate@example.com")
    # Launch
    launch_res = client.post("/api/v1/labs/linux/launch", headers=headers)
    session_id = launch_res.json()["id"]

    # Validate Task 3 (touch note.txt) - should fail initially
    val_res = client.post(
        f"/api/v1/labs/linux/{session_id}/validate",
        headers=headers,
        json={"task_id": 3}
    )
    assert val_res.status_code == 200
    assert val_res.json()["success"] is False

    # Simulate command execution by creating file in session scratch directory
    scratch_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), f"../scratch/sessions/{session_id}/home/student/note.txt")
    )
    # Simulate command execution by creating file in session scratch directory
    scratch_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), f"../scratch/sessions/{session_id}/home/student/note.txt")
    )
    os.makedirs(os.path.dirname(scratch_path), exist_ok=True)
    with open(scratch_path, "w") as f:
        f.write("")

    # Validate again - should now succeed
    val_res2 = client.post(
        f"/api/v1/labs/linux/{session_id}/validate",
        headers=headers,
        json={"task_id": 3}
    )
    assert val_res2.status_code == 200
    assert val_res2.json()["success"] is True

    # Cleanup test session files
    from app.services.runtime import runtime_service
    runtime_service.stop_lab(session_id)
