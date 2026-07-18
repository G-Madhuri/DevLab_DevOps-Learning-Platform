import os
import shutil
import pytest
from app.services.runtime import runtime_service
from app.services.validation import validation_engine


def test_github_actions_session_lifecycle():
    """
    Verifies that GitHubActionsRuntime provisions repositories and remote origins.
    """
    session_id = "actions_test_lifecycle"
    res = runtime_service.create_lab(session_id, lab_name="github-actions-fundamentals")
    assert res["status"] == "running"
    assert res["mode"] == "actions"

    shell = runtime_service.get_session_shell(session_id, lab_name="github-actions-fundamentals")
    assert shell is not None
    assert os.path.exists(shell.base_dir)

    # Check git init has run
    assert os.path.exists(os.path.join(shell.base_dir, ".git"))

    # Cleanup
    runtime_service.stop_lab(session_id, container_id=res["container_id"], lab_name="github-actions-fundamentals")
    assert not os.path.exists(shell.base_dir)


def test_github_actions_validation_and_challenges():
    """
    Verifies that ValidationEngine checks YAML configurations and intercepts push commands.
    """
    session_id = "actions_val_test"
    runtime_service.stop_lab(session_id, container_id=f"actions-{session_id}", lab_name="github-actions-fundamentals")

    try:
        runtime_service.create_lab(session_id, lab_name="github-actions-fundamentals")
        shell = runtime_service.get_session_shell(session_id, lab_name="github-actions-fundamentals")
        assert shell is not None

        # Step 1 verification fails because workflow file does not exist
        res1_fail = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"actions-{session_id}",
            task_id=1,
            mode="actions",
            lab_name="github-actions-fundamentals"
        )
        assert res1_fail["success"] is False

        # Create workflow file
        workflow_dir = os.path.join(shell.base_dir, ".github", "workflows")
        os.makedirs(workflow_dir, exist_ok=True)
        workflow_file = os.path.join(workflow_dir, "main.yml")
        
        with open(workflow_file, "w") as f:
            f.write(
                "name: Welcome Workflow\n"
                "on: [push]\n"
                "jobs:\n"
                "  welcome:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - name: Say Hello\n"
                "        run: echo 'Welcome!'\n"
            )

        res1_success = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"actions-{session_id}",
            task_id=1,
            mode="actions",
            lab_name="github-actions-fundamentals"
        )
        assert res1_success["success"] is True

        # Challenge step 8 fails before git push
        res8_fail = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"actions-{session_id}",
            task_id=8,
            mode="actions",
            lab_name="github-actions-fundamentals"
        )
        assert res8_fail["success"] is False

        # Add & commit files
        shell.execute_command("git add .github/workflows/main.yml")
        shell.execute_command('git commit -m "feat: configure welcome workflow"')
        
        # Run git push - triggers workflow execution simulation!
        res_push_log = shell.execute_command("git push origin main")
        assert "GitHub Actions" in res_push_log
        assert "Workflow completed successfully!" in res_push_log

        # Step 8 validation passes after workflow execution
        res8_success = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"actions-{session_id}",
            task_id=8,
            mode="actions",
            lab_name="github-actions-fundamentals"
        )
        assert res8_success["success"] is True

    finally:
        runtime_service.stop_lab(session_id, container_id=f"actions-{session_id}", lab_name="github-actions-fundamentals")
