import pytest
from app.courses.engine import course_engine
from app.services.runtime import runtime_service, SimulatedKubernetesShell
from app.services.validation import validation_engine

def test_kubernetes_course_engine():
    """
    Verifies that course_engine dynamically loads modular Kubernetes courses config files.
    """
    pods_lessons = course_engine.get_lessons("kubernetes-pods")
    assert len(pods_lessons) == 8
    assert pods_lessons[0]["id"] == 1
    assert "nginx-pod" in pods_lessons[0]["instruction"]

    fundamentals_lessons = course_engine.get_lessons("kubernetes-fundamentals")
    assert len(fundamentals_lessons) == 8
    assert "kubectl get nodes" in fundamentals_lessons[0]["instruction"]

    capstone_lessons = course_engine.get_lessons("kubernetes-capstone-project")
    assert len(capstone_lessons) == 8


def test_kubernetes_runtime_fallback():
    """
    Verifies that KubernetesRuntime falls back to simulated/mock mode when no K3s is active.
    """
    session_id = "k8s_test_session"
    res = runtime_service.create_lab(session_id, lab_name="kubernetes-pods")
    assert res["status"] == "running"
    assert res["mode"] == "simulated"
    assert res["container_id"] == f"simulated-{session_id}"

    shell = runtime_service.get_session_shell(session_id, lab_name="kubernetes-pods")
    assert isinstance(shell, SimulatedKubernetesShell)

    # Clean up
    runtime_service.stop_lab(session_id, container_id=res["container_id"], lab_name="kubernetes-pods")


def test_kubernetes_validation_simulated():
    """
    Verifies that ValidationEngine evaluates Kubernetes student tasks correctly in simulated mode.
    """
    session_id = "k8s_val_session"
    runtime_service.create_lab(session_id, lab_name="kubernetes-pods")
    shell = runtime_service.get_session_shell(session_id, lab_name="kubernetes-pods")
    assert shell is not None

    # Step 1 auto-verification
    res1 = validation_engine.validate_task(
        session_id=session_id,
        container_id=f"simulated-{session_id}",
        task_id=1,
        mode="simulated",
        lab_name="kubernetes-pods"
    )
    assert res1["success"] is True

    # Step 8 (Mini Challenge) fails if resource is not created
    res8_fail = validation_engine.validate_task(
        session_id=session_id,
        container_id=f"simulated-{session_id}",
        task_id=8,
        mode="simulated",
        lab_name="kubernetes-pods"
    )
    assert res8_fail["success"] is False

    # Simulate creation of the challenge resource
    shell.execute_command("kubectl apply -f pod.yaml")
    # Set the mockup pod directly
    shell.mock_pods["custom-pod"] = {"image": "redis:alpine", "status": "Running"}

    res8_success = validation_engine.validate_task(
        session_id=session_id,
        container_id=f"simulated-{session_id}",
        task_id=8,
        mode="simulated",
        lab_name="kubernetes-pods"
    )
    assert res8_success["success"] is True

    # Clean up
    runtime_service.stop_lab(session_id, container_id=f"simulated-{session_id}", lab_name="kubernetes-pods")
