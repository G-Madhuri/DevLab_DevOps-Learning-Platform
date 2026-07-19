import os
import shutil
import pytest
from app.services.runtime import runtime_service
from app.services.validation import validation_engine


def test_ansible_session_lifecycle():
    """
    Verifies that AnsibleRuntime provisions workspaces and cleans them up.
    """
    session_id = "ansible_test_lifecycle"
    res = runtime_service.create_lab(session_id, lab_name="introduction-to-ansible")
    assert res["status"] == "running"
    assert res["mode"] == "ansible"

    shell = runtime_service.get_session_shell(session_id, lab_name="introduction-to-ansible")
    assert shell is not None
    assert os.path.exists(shell.base_dir)

    # Check hosts template file was created
    assert os.path.exists(os.path.join(shell.base_dir, "hosts"))
    assert os.path.exists(os.path.join(shell.base_dir, "playbook.yml"))

    # Cleanup
    runtime_service.stop_lab(session_id, container_id=res["container_id"], lab_name="introduction-to-ansible")
    assert not os.path.exists(shell.base_dir)


def test_ansible_commands_simulation():
    """
    Verifies that AnsibleShell correctly parses and executes custom Ansible CLI simulator subcommands.
    """
    session_id = "ansible_test_cli"
    runtime_service.stop_lab(session_id, container_id=f"ansible-{session_id}", lab_name="introduction-to-ansible")

    try:
        runtime_service.create_lab(session_id, lab_name="introduction-to-ansible")
        shell = runtime_service.get_session_shell(session_id, lab_name="introduction-to-ansible")
        assert shell is not None

        # 1. Test ping ad-hoc module
        ping_res = shell.execute_command("ansible all -i hosts -m ping")
        assert "localhost | SUCCESS => {" in ping_res
        assert '"ping": "pong"' in ping_res

        # 2. Test shell uptime command
        uptime_res = shell.execute_command("ansible all -i hosts -m shell -a \"uptime\"")
        assert "localhost | CHANGED | rc=0 >>" in uptime_res
        assert "load average" in uptime_res

        # 3. Test galaxy role init
        galaxy_res = shell.execute_command("ansible-galaxy role init roles/web")
        assert "- web was created successfully" in galaxy_res
        assert os.path.exists(os.path.join(shell.base_dir, "roles/web/tasks/main.yml"))

        # 4. Test playbook syntax dry run
        syntax_res = shell.execute_command("ansible-playbook playbook.yml --syntax-check")
        assert "playbook: playbook.yml" in syntax_res

        # 5. Test playbook execution simulation
        run_res = shell.execute_command("ansible-playbook playbook.yml")
        assert "PLAY [DevLab Ansible Playground]" in run_res
        assert "TASK [Gathering Facts]" in run_res
        assert "PLAY RECAP" in run_res

        # 6. Test inventory listing
        inv_res = shell.execute_command("ansible-inventory -i hosts --list")
        assert '"webservers": {' in inv_res
        assert '"localhost"' in inv_res

        # 7. Test doc print help
        doc_res = shell.execute_command("ansible-doc ping")
        assert "> PING" in doc_res

    finally:
        runtime_service.stop_lab(session_id, container_id=f"ansible-{session_id}", lab_name="introduction-to-ansible")


def test_ansible_validators_logic():
    """
    Verifies that ValidationEngine correctly grades progress on Ansible modules.
    """
    session_id = "ansible_test_val"
    runtime_service.stop_lab(session_id, container_id=f"ansible-{session_id}", lab_name="introduction-to-ansible")

    try:
        runtime_service.create_lab(session_id, lab_name="introduction-to-ansible")
        shell = runtime_service.get_session_shell(session_id, lab_name="introduction-to-ansible")
        assert shell is not None

        # Task 1: Check File configuration created
        val_res = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"ansible-{session_id}",
            task_id=1,
            mode="ansible",
            lab_name="introduction-to-ansible"
        )
        assert val_res["success"] is True

        # Task 2: Diagnostics run (pwd or version in history)
        shell.execute_command("pwd")
        val_res = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"ansible-{session_id}",
            task_id=2,
            mode="ansible",
            lab_name="introduction-to-ansible"
        )
        assert val_res["success"] is True

        # Task 8: Module specific checks (introduction-to-ansible require ansible-doc ping)
        val_res = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"ansible-{session_id}",
            task_id=8,
            mode="ansible",
            lab_name="introduction-to-ansible"
        )
        assert val_res["success"] is False

        shell.execute_command("ansible-doc ping")
        val_res = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"ansible-{session_id}",
            task_id=8,
            mode="ansible",
            lab_name="introduction-to-ansible"
        )
        assert val_res["success"] is True

    finally:
        runtime_service.stop_lab(session_id, container_id=f"ansible-{session_id}", lab_name="introduction-to-ansible")
