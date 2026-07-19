import os
import shutil
import pytest
from app.services.runtime import runtime_service
from app.services.validation import validation_engine


def test_jenkins_session_lifecycle():
    """
    Verifies that JenkinsRuntime provisions repositories.
    """
    session_id = "jenkins_test_lifecycle"
    res = runtime_service.create_lab(session_id, lab_name="jenkins-fundamentals")
    assert res["status"] == "running"
    assert res["mode"] == "jenkins"

    shell = runtime_service.get_session_shell(session_id, lab_name="jenkins-fundamentals")
    assert shell is not None
    assert os.path.exists(shell.base_dir)

    # Check git init has run
    assert os.path.exists(os.path.join(shell.base_dir, ".git"))

    # Cleanup
    runtime_service.stop_lab(session_id, container_id=res["container_id"], lab_name="jenkins-fundamentals")
    assert not os.path.exists(shell.base_dir)


def test_jenkins_validation_and_challenges():
    """
    Verifies that ValidationEngine checks Jenkinsfile configurations and runs custom jenkins command.
    """
    session_id = "jenkins_val_test"
    runtime_service.stop_lab(session_id, container_id=f"jenkins-{session_id}", lab_name="jenkins-fundamentals")

    try:
        runtime_service.create_lab(session_id, lab_name="jenkins-fundamentals")
        shell = runtime_service.get_session_shell(session_id, lab_name="jenkins-fundamentals")
        assert shell is not None

        # Step 1 verification fails because Jenkinsfile does not exist
        res1_fail = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"jenkins-{session_id}",
            task_id=1,
            mode="jenkins",
            lab_name="jenkins-fundamentals"
        )
        assert res1_fail["success"] is False

        # Create Jenkinsfile file
        jenkinsfile = os.path.join(shell.base_dir, "Jenkinsfile")
        with open(jenkinsfile, "w") as f:
            f.write(
                "pipeline {\n"
                "  agent any\n"
                "  stages {\n"
                "    stage('Build') {\n"
                "      steps {\n"
                "        echo 'Building...'\n"
                "      }\n"
                "    }\n"
                "  }\n"
                "}"
            )

        res1_success = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"jenkins-{session_id}",
            task_id=1,
            mode="jenkins",
            lab_name="jenkins-fundamentals"
        )
        assert res1_success["success"] is True

        # Challenge step 8 fails before jenkins build command
        res8_fail = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"jenkins-{session_id}",
            task_id=8,
            mode="jenkins",
            lab_name="jenkins-fundamentals"
        )
        assert res8_fail["success"] is False

        # Run custom jenkins tool
        res_run_log = shell.execute_command("jenkins build")
        assert "Jenkins" in res_run_log
        assert "Pipeline completed successfully!" in res_run_log

        # Step 8 validation passes after pipeline execution
        res8_success = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"jenkins-{session_id}",
            task_id=8,
            mode="jenkins",
            lab_name="jenkins-fundamentals"
        )
        assert res8_success["success"] is True

    finally:
        runtime_service.stop_lab(session_id, container_id=f"jenkins-{session_id}", lab_name="jenkins-fundamentals")
