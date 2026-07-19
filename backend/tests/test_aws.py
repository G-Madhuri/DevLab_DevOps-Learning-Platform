import os
import shutil
import pytest
from app.services.runtime import runtime_service
from app.services.validation import validation_engine


def test_aws_session_lifecycle():
    """
    Verifies that AWSRuntime provisions workspaces and cleans them up.
    """
    session_id = "aws_test_lifecycle"
    res = runtime_service.create_lab(session_id, lab_name="aws-cloud-fundamentals")
    assert res["status"] == "running"
    assert res["mode"] == "aws"

    shell = runtime_service.get_session_shell(session_id, lab_name="aws-cloud-fundamentals")
    assert shell is not None
    assert os.path.exists(shell.base_dir)

    # Check hosts template file was created
    assert os.path.exists(os.path.join(shell.base_dir, "main.tf"))

    # Cleanup
    runtime_service.stop_lab(session_id, container_id=res["container_id"], lab_name="aws-cloud-fundamentals")
    assert not os.path.exists(shell.base_dir)


def test_aws_commands_simulation():
    """
    Verifies that AWSShell correctly parses and executes custom AWS CLI simulator subcommands.
    """
    session_id = "aws_test_cli"
    runtime_service.stop_lab(session_id, container_id=f"aws-{session_id}", lab_name="aws-cloud-fundamentals")

    try:
        runtime_service.create_lab(session_id, lab_name="aws-cloud-fundamentals")
        shell = runtime_service.get_session_shell(session_id, lab_name="aws-cloud-fundamentals")
        assert shell is not None

        # 1. Test version check
        ver_res = shell.execute_command("aws --version")
        assert "aws-cli/" in ver_res

        # 2. Test configure list
        config_res = shell.execute_command("aws configure list")
        assert "access_key" in config_res
        assert "secret_key" in config_res

        # 3. Test iam create-user
        user_res = shell.execute_command("aws iam create-user --user-name devlab-admin")
        assert '"UserName": "devlab-admin"' in user_res
        assert "arn:aws:iam::" in user_res

        # 4. Test list users
        list_user_res = shell.execute_command("aws iam list-users")
        assert '"UserName": "devlab-admin"' in list_user_res

        # 5. Test ec2 create-vpc
        vpc_res = shell.execute_command("aws ec2 create-vpc --cidr-block 10.0.0.0/16")
        assert "vpc-" in vpc_res
        assert "available" in vpc_res

        # 6. Test ec2 create-subnet
        subnet_res = shell.execute_command("aws ec2 create-subnet --cidr-block 10.0.1.0/24")
        assert "subnet-" in subnet_res
        assert "available" in subnet_res

        # 7. Test ec2 run-instances
        run_res = shell.execute_command("aws ec2 run-instances --image-id ami-12345 --instance-type t2.micro")
        assert "InstanceId" in run_res
        assert "running" in run_res

        # 8. Test ec2 describe-instances
        desc_res = shell.execute_command("aws ec2 describe-instances")
        assert "InstanceId" in desc_res

        # 9. Test s3 mb
        s3_res = shell.execute_command("aws s3 mb s3://devlab-test-bucket")
        assert "make_bucket: s3://devlab-test-bucket" in s3_res
        assert os.path.exists(os.path.join(shell.base_dir, "devlab-test-bucket"))

        # 10. Test s3 cp
        with open(os.path.join(shell.base_dir, "local.txt"), "w") as lf:
            lf.write("hello")
        cp_res = shell.execute_command("aws s3 cp local.txt s3://devlab-test-bucket/remote.txt")
        assert "upload:" in cp_res
        assert os.path.exists(os.path.join(shell.base_dir, "devlab-test-bucket/remote.txt"))

        # 11. Test s3 ls
        ls_res = shell.execute_command("aws s3 ls")
        assert "devlab-test-bucket" in ls_res

        # 12. Test rds create-db
        rds_res = shell.execute_command("aws rds create-db-instance --db-instance-identifier devlab-db")
        assert "creating" in rds_res
        assert "postgres" in rds_res

        # 13. Test rds describe-db
        rds_desc = shell.execute_command("aws rds describe-db-instances")
        assert "available" in rds_desc

        # 14. Test elbv2
        alb_res = shell.execute_command("aws elbv2 create-load-balancer --name devlab-alb")
        assert "devlab-alb" in alb_res
        assert "active" in alb_res

        # 15. Test autoscaling
        asg_res = shell.execute_command("aws autoscaling create-auto-scaling-group --auto-scaling-group-name devlab-asg")
        assert "successfully created" in asg_res

        # 16. Test cloudwatch
        cw_res = shell.execute_command("aws cloudwatch put-metric-alarm --alarm-name cpu-alarm")
        assert "successfully created" in cw_res
        cw_desc = shell.execute_command("aws cloudwatch describe-alarms")
        assert "cpu-alarm" in cw_desc

        # 17. Test ssh
        ssh_res = shell.execute_command("ssh student@127.0.0.1")
        assert "closed" in ssh_res

        # 18. Test curl
        curl_res = shell.execute_command("curl http://localhost")
        assert "Welcome to AWS Production Web App!" in curl_res

    finally:
        runtime_service.stop_lab(session_id, container_id=f"aws-{session_id}", lab_name="aws-cloud-fundamentals")


def test_aws_validators_logic():
    """
    Verifies that ValidationEngine correctly grades progress on AWS modules.
    """
    session_id = "aws_test_val"
    runtime_service.stop_lab(session_id, container_id=f"aws-{session_id}", lab_name="aws-cloud-fundamentals")

    try:
        runtime_service.create_lab(session_id, lab_name="aws-cloud-fundamentals")
        shell = runtime_service.get_session_shell(session_id, lab_name="aws-cloud-fundamentals")
        assert shell is not None

        # Task 1: Initialize first files check
        val_res = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"aws-{session_id}",
            task_id=1,
            mode="aws",
            lab_name="aws-cloud-fundamentals"
        )
        assert val_res["success"] is True

        # Task 2: Diagnostics run
        shell.execute_command("pwd")
        val_res = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"aws-{session_id}",
            task_id=2,
            mode="aws",
            lab_name="aws-cloud-fundamentals"
        )
        assert val_res["success"] is True

        # Task 8: Module specific check (aws-cloud-fundamentals require aws configure list)
        val_res = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"aws-{session_id}",
            task_id=8,
            mode="aws",
            lab_name="aws-cloud-fundamentals"
        )
        assert val_res["success"] is False

        shell.execute_command("aws configure list")
        val_res = validation_engine.validate_task(
            session_id=session_id,
            container_id=f"aws-{session_id}",
            task_id=8,
            mode="aws",
            lab_name="aws-cloud-fundamentals"
        )
        assert val_res["success"] is True

    finally:
        runtime_service.stop_lab(session_id, container_id=f"aws-{session_id}", lab_name="aws-cloud-fundamentals")
