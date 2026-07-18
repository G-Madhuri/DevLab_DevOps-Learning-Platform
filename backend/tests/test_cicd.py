import os
import shutil
import pytest
from app.services.runtime import runtime_service
from app.services.validation import validation_engine


def test_cicd_session_lifecycle():
    """
    Verifies that CICDRuntime provisions repositories.
    """
    session_id = "cicd_test_lifecycle"
    res = runtime_service.create_lab(session_id, lab_name="introduction-to-cicd")
    assert res["status"] == "running"
    assert res["mode"] == "cicd"

    shell = runtime_service.get_session_shell(session_id, lab_name="introduction-to-cicd")
    assert shell is not None
    assert os.path.exists(shell.base_dir)

    # Check git init has run
    assert os.path.exists(os.path.join(shell.base_dir, ".git"))

    # Cleanup
    runtime_service.stop_lab(session_id, container_id=res["container_id"], lab_name="introduction-to-cicd")
    assert not os.path.exists(shell.base_dir)


def test_cicd_validation_and_challenges():
    """
    Verifies that ValidationEngine checks pipeline.yml configurations and runs custom pipeline command.
    """
    session_id = "cicd_val_test"
    runtime_service.stop_lab(session_id, container_id=f"cicd-{session_id}", lab_name="introduction-to-cicd")

    try:
        runtime_service.create_lab(session_id, lab_name="introduction-to-cicd")
        shell = runtime_service.get_session_shell(session_id, lab_name="introduction-to-cicd")
        assert shell is not None

        # Step 1 verification fails because pipeline file does not exist
        res1_fail = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"cicd-{session_id}",
            task_id=1,
            mode="cicd",
            lab_name="introduction-to-cicd"
        )
        assert res1_fail["success"] is False

        # Create pipeline file
        pipeline_file = os.path.join(shell.base_dir, "pipeline.yml")
        with open(pipeline_file, "w") as f:
            f.write(
                "stages:\n"
                "  - checkout\n"
                "  - test\n"
                "  - build\n"
            )

        res1_success = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"cicd-{session_id}",
            task_id=1,
            mode="cicd",
            lab_name="introduction-to-cicd"
        )
        assert res1_success["success"] is True

        # Challenge step 8 fails before run-pipeline command
        res8_fail = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"cicd-{session_id}",
            task_id=8,
            mode="cicd",
            lab_name="introduction-to-cicd"
        )
        assert res8_fail["success"] is False

        # Run custom pipeline tool - triggers simulator execution logs!
        res_run_log = shell.execute_command("run-pipeline")
        assert "Pipeline" in res_run_log
        assert "Pipeline completed successfully!" in res_run_log

        # Step 8 validation passes after pipeline execution
        res8_success = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"cicd-{session_id}",
            task_id=8,
            mode="cicd",
            lab_name="introduction-to-cicd"
        )
        assert res8_success["success"] is True

    finally:
        runtime_service.stop_lab(session_id, container_id=f"cicd-{session_id}", lab_name="introduction-to-cicd")
