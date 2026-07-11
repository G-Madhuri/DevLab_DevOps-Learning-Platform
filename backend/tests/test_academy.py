import pytest
import os
from app.models.progress import CourseProgress
from app.services.runtime import runtime_service
from app.services.validation import validation_engine


def get_auth_headers(client, email="user@example.com", password="Password123!"):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": "Test User",
            "password": password,
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "username": email,
            "password": password,
        },
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_academies_list_unauthorized(client):
    """
    Test that retrieving academies requires auth.
    """
    response = client.get("/api/v1/labs/academies/list")
    assert response.status_code == 401


def test_academies_list_authorized(client, db):
    """
    Test retrieving academies with auth and checking default progress.
    """
    headers = get_auth_headers(client, "auth@example.com")
    response = client.get("/api/v1/labs/academies/list", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Assert academies present
    linux_academy = next((a for a in data if a["id"] == "linux"), None)
    assert linux_academy is not None
    assert linux_academy["title"] == "Linux Academy"
    assert linux_academy["coming_soon"] is False
    assert linux_academy["progress"] == 0
    assert linux_academy["certificate_status"] == "locked"
    
    # Verify course structure
    courses = linux_academy["courses"]
    assert len(courses) == 5
    assert courses[0]["slug"] == "linux-command-line-basics"
    assert courses[4]["slug"] == "linux-capstone-project"
    assert courses[4]["is_capstone"] is True


def test_certificate_unlock_logic(client, db):
    """
    Test that the certificate unlocks only when all courses inside an academy are 100% completed.
    """
    headers = get_auth_headers(client, "cert@example.com")
    
    # Verify it is locked initially
    res = client.get("/api/v1/labs/academies/detail/linux", headers=headers)
    assert res.json()["certificate_status"] == "locked"
    assert res.json()["certificate_unlocked"] is False

    # Simulate 100% completion of first 4 courses
    from app.models.user import User
    user = db.query(User).filter(User.email == "cert@example.com").first()
    
    course_slugs = [
        "linux-command-line-basics",
        "linux-file-system-permissions",
        "bash-scripting-fundamentals",
        "linux-networking-processes",
        "linux-capstone-project"
    ]
    
    for slug in course_slugs[:-1]:
        prog = CourseProgress(
            user_id=user.id,
            course_slug=slug,
            completed_lessons=[i for i in range(1, 16)],
            current_lesson_id=16,
            percentage=100
        )
        db.add(prog)
    db.commit()

    # Still locked since capstone is not complete
    res = client.get("/api/v1/labs/academies/detail/linux", headers=headers)
    assert res.json()["certificate_status"] == "locked"

    # Complete the capstone
    capstone_prog = CourseProgress(
        user_id=user.id,
        course_slug="linux-capstone-project",
        completed_lessons=[i for i in range(1, 16)],
        current_lesson_id=16,
        percentage=100
    )
    db.add(capstone_prog)
    db.commit()

    # Now it should be unlocked!
    res = client.get("/api/v1/labs/academies/detail/linux", headers=headers)
    assert res.json()["certificate_status"] == "unlocked"
    assert res.json()["certificate_unlocked"] is True

    # Generate certificate
    gen_res = client.post("/api/v1/labs/academies/detail/linux/certificate/generate", headers=headers)
    assert gen_res.status_code == 200
    assert gen_res.json()["success"] is True
    assert "certificate_id" in gen_res.json()


def test_linux_runtime_and_validation(db):
    """
    Test runtime command executions and simulated validation engine logic.
    """
    session_id = "test-session-12345"
    # Create lab simulation
    res = runtime_service.create_lab(session_id, "linux-command-line-basics")
    assert res["mode"] == "simulated"
    
    shell = runtime_service.get_session_shell(session_id, "linux-command-line-basics")
    assert shell is not None
    
    # Run pwd
    out = shell.execute_command("pwd")
    assert "/home/student" in out
    
    # Run touch and ls
    shell.execute_command("touch draft.txt")
    out = shell.execute_command("ls")
    assert "draft.txt" in out

    # Test validator for Touch task
    val_res = validation_engine.validate_task(
        session_id=session_id,
        container_id=f"simulated-{session_id}",
        task_id=8,
        mode="simulated",
        lab_name="linux-command-line-basics"
    )
    assert val_res["success"] is True

    # Clean up
    runtime_service.stop_lab(session_id, res["container_id"], "linux-command-line-basics")
    assert not os.path.exists(shell.base_dir)


def test_bash_interpreter_simulation():
    """
    Test that SimulatedShell runs basic bash scripts correctly.
    """
    session_id = "test-bash-session"
    runtime_service.create_lab(session_id, "bash-scripting-fundamentals")
    shell = runtime_service.get_session_shell(session_id)
    
    # Write a simple script
    script_path = shell.get_local_path("test.sh")
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\nVAR=10\necho $VAR\npwd\n")
        
    out = shell.execute_command("bash test.sh")
    assert "10" in out
    assert "/home/student" in out
    
    runtime_service.stop_lab(session_id, f"simulated-{session_id}", "bash-scripting-fundamentals")


def test_course_details(client, db):
    """
    Test that retrieving detailed course specifications returns structure keys.
    """
    headers = get_auth_headers(client, "details@example.com")
    response = client.get("/api/v1/labs/linux/linux-command-line-basics/details", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "linux-command-line-basics"
    assert "theory" in data
    assert "interactive_examples" in data
    assert "exercises" in data
    assert "quiz" in data
    assert len(data["lessons"]) == 15
    assert len(data["quiz"]) == 3
