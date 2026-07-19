import os
import shutil
import pytest
from app.services.runtime import runtime_service
from app.services.validation import validation_engine


def test_terraform_session_lifecycle():
    """
    Verifies that TerraformRuntime provisions workspaces and cleans them up.
    """
    session_id = "terraform_test_lifecycle"
    res = runtime_service.create_lab(session_id, lab_name="terraform-fundamentals")
    assert res["status"] == "running"
    assert res["mode"] == "terraform"

    shell = runtime_service.get_session_shell(session_id, lab_name="terraform-fundamentals")
    assert shell is not None
    assert os.path.exists(shell.base_dir)

    # Check main.tf template file was created
    assert os.path.exists(os.path.join(shell.base_dir, "main.tf"))

    # Cleanup
    runtime_service.stop_lab(session_id, container_id=res["container_id"], lab_name="terraform-fundamentals")
    assert not os.path.exists(shell.base_dir)


def test_terraform_commands_simulation():
    """
    Verifies that TerraformShell correctly parses and executes custom terraform CLI simulator subcommands.
    """
    session_id = "terraform_test_cli"
    runtime_service.stop_lab(session_id, container_id=f"terraform-{session_id}", lab_name="terraform-fundamentals")

    try:
        runtime_service.create_lab(session_id, lab_name="terraform-fundamentals")
        shell = runtime_service.get_session_shell(session_id, lab_name="terraform-fundamentals")
        assert shell is not None

        # 1. Uninitialized terraform plan fails
        plan_uninit = shell.execute_command("terraform plan")
        assert "Error: Terraform not initialized" in plan_uninit

        # 2. terraform init download plugins
        init_res = shell.execute_command("terraform init")
        assert "Initializing provider plugins..." in init_res
        assert "successfully initialized!" in init_res
        assert os.path.exists(os.path.join(shell.base_dir, ".terraform"))

        # 3. Write dummy HCL file
        main_tf = os.path.join(shell.base_dir, "main.tf")
        with open(main_tf, "w") as f:
            f.write(
                'resource "local_file" "welcome" {\n'
                '  filename = "welcome.txt"\n'
                '  content  = "Welcome to Terraform!"\n'
                '}\n'
            )

        # 4. terraform validate syntax success
        validate_res = shell.execute_command("terraform validate")
        assert "Success! The configuration is valid." in validate_res

        # 5. terraform plan outputs action steps
        plan_res = shell.execute_command("terraform plan")
        assert "local_file.welcome" in plan_res
        assert "Plan:" in plan_res

        # 6. terraform apply generates tfstate
        apply_res = shell.execute_command("terraform apply")
        assert "local_file.welcome: Creation complete" in apply_res
        assert "Apply complete!" in apply_res
        assert os.path.exists(os.path.join(shell.base_dir, "terraform.tfstate"))

        # 7. terraform state list parses tfstate resources
        state_list = shell.execute_command("terraform state list")
        assert "local_file.welcome" in state_list

        # 8. Workspace subcommands
        workspace_list = shell.execute_command("terraform workspace list")
        assert "* default" in workspace_list

        workspace_new = shell.execute_command("terraform workspace new dev")
        assert "Created and switched to workspace \"dev\"!" in workspace_new

        workspace_select = shell.execute_command("terraform workspace select default")
        assert "Switched to workspace \"default\"!" in workspace_select

    finally:
        runtime_service.stop_lab(session_id, container_id=f"terraform-{session_id}", lab_name="terraform-fundamentals")


def test_terraform_validators_logic():
    """
    Verifies that ValidationEngine correctly grades progress on each of the 11 Terraform modules.
    """
    session_id = "terraform_test_val"
    runtime_service.stop_lab(session_id, container_id=f"terraform-{session_id}", lab_name="terraform-fundamentals")

    try:
        runtime_service.create_lab(session_id, lab_name="terraform-fundamentals")
        shell = runtime_service.get_session_shell(session_id, lab_name="terraform-fundamentals")
        assert shell is not None

        # Write dummy HCL file resource so init finds configuration files
        main_tf = os.path.join(shell.base_dir, "main.tf")
        with open(main_tf, "w") as f:
            f.write(
                'resource "local_file" "welcome" {\n'
                '  filename = "welcome.txt"\n'
                '  content  = "Welcome to Terraform!"\n'
                '}\n'
            )

        # Run init so subsequent commands are allowed
        shell.execute_command("terraform init")

        # Task 1 (main.tf file check)
        val1 = validation_engine.validate_task(session_id, f"terraform-{session_id}", 1, "terraform", "terraform-fundamentals")
        assert val1["success"] is True

        # Task 2 (terraform validate check)
        shell.execute_command("terraform validate")
        val2 = validation_engine.validate_task(session_id, f"terraform-{session_id}", 2, "terraform", "terraform-fundamentals")
        assert val2["success"] is True

        # Task 3 (terraform plan check)
        shell.execute_command("terraform plan")
        val3 = validation_engine.validate_task(session_id, f"terraform-{session_id}", 3, "terraform", "terraform-fundamentals")
        assert val3["success"] is True

        # Task 4 (terraform apply check)
        shell.execute_command("terraform apply")
        val4 = validation_engine.validate_task(session_id, f"terraform-{session_id}", 4, "terraform", "terraform-fundamentals")
        assert val4["success"] is True

        # Task 5 (terraform workspace select dev check)
        shell.execute_command("terraform workspace new dev")
        shell.execute_command("terraform workspace select dev")
        val5 = validation_engine.validate_task(session_id, f"terraform-{session_id}", 5, "terraform", "terraform-fundamentals")
        assert val5["success"] is True

        # Task 6 (terraform state list check)
        shell.execute_command("terraform state list")
        val6 = validation_engine.validate_task(session_id, f"terraform-{session_id}", 6, "terraform", "terraform-fundamentals")
        assert val6["success"] is True

        # Task 7 (terraform output check)
        shell.execute_command("terraform output")
        val7 = validation_engine.validate_task(session_id, f"terraform-{session_id}", 7, "terraform", "terraform-fundamentals")
        assert val7["success"] is True

        # Task 8 (Mini Challenge Fundamentals)
        val8 = validation_engine.validate_task(session_id, f"terraform-{session_id}", 8, "terraform", "terraform-fundamentals")
        assert val8["success"] is True

    finally:
        runtime_service.stop_lab(session_id, container_id=f"terraform-{session_id}", lab_name="terraform-fundamentals")
