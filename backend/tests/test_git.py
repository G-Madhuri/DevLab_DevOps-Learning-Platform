import pytest
import os
from app.courses.engine import course_engine
from app.services.runtime import runtime_service, GitShell
from app.services.validation import validation_engine

def test_git_course_engine():
    """
    Verifies that course_engine dynamically loads modular Git courses config files.
    """
    fundamentals_lessons = course_engine.get_lessons("git-fundamentals")
    assert len(fundamentals_lessons) == 8
    assert "git init" in fundamentals_lessons[0]["example"]

    branching_lessons = course_engine.get_lessons("git-branching-and-merging")
    assert len(branching_lessons) == 8
    assert "git branch" in branching_lessons[0]["example"]


def test_git_runtime_instantiation():
    """
    Verifies that GitRuntime creates an isolated local Git repository directory.
    """
    session_id = "git_test_session"
    res = runtime_service.create_lab(session_id, lab_name="git-fundamentals")
    assert res["status"] == "running"
    assert res["mode"] == "git"
    assert res["container_id"] == f"git-{session_id}"

    shell = runtime_service.get_session_shell(session_id, lab_name="git-fundamentals")
    assert isinstance(shell, GitShell)
    assert os.path.exists(shell.base_dir)
    assert os.path.exists(os.path.join(shell.base_dir, ".git"))

    # Clean up
    runtime_service.stop_lab(session_id, container_id=res["container_id"], lab_name="git-fundamentals")
    assert not os.path.exists(shell.base_dir)


def test_git_validation_and_challenges():
    """
    Verifies that ValidationEngine evaluates Git student tasks and challenges correctly.
    """
    session_id = "git_val_session_unique"
    
    # Pre-cleanup in case of previous failures
    runtime_service.stop_lab(session_id, container_id=f"git-{session_id}", lab_name="git-fundamentals")
    
    try:
        runtime_service.create_lab(session_id, lab_name="git-fundamentals")
        shell = runtime_service.get_session_shell(session_id, lab_name="git-fundamentals")
        assert shell is not None

        # Step 2 verification fails before git status is run
        res2_fail = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"git-{session_id}",
            task_id=2,
            mode="git",
            lab_name="git-fundamentals"
        )
        assert res2_fail["success"] is False

        # Simulate running status
        shell.execute_command("git status")
        res2_success = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"git-{session_id}",
            task_id=2,
            mode="git",
            lab_name="git-fundamentals"
        )
        assert res2_success["success"] is True

        # Step 8 (Mini Challenge) fails if index.html is missing
        res8_fail = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"git-{session_id}",
            task_id=8,
            mode="git",
            lab_name="git-fundamentals"
        )
        assert res8_fail["success"] is False

        # Run the challenge command via shell to simulate student completing the task
        shell.execute_command('echo ^<h1^>DevLab^</h1^> > index.html')
        shell.execute_command("git add index.html")
        shell.execute_command('git commit -m "feat: initial page"')

        res8_success = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"git-{session_id}",
            task_id=8,
            mode="git",
            lab_name="git-fundamentals"
        )
        assert res8_success["success"] is True
    finally:
        # Clean up
        runtime_service.stop_lab(session_id, container_id=f"git-{session_id}", lab_name="git-fundamentals")
