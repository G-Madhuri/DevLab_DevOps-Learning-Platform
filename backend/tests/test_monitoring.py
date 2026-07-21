import pytest
import os
import json
from app.services.runtime import MonitoringShell, MonitoringRuntime
from app.services.validation import validation_engine

def test_monitoring_shell_commands():
    shell = MonitoringShell(session_id="test-mon-123")
    
    # 1. Whitelist validation
    unallowed = shell.execute_command("malicious_tool --hack")
    assert "command not allowed" in unallowed

    # 2. Promtool command check
    prom_res = shell.execute_command("promtool check config prometheus.yml")
    assert "SUCCESS" in prom_res

    # 3. Amtool check
    am_res = shell.execute_command("amtool check-config alertmanager.yml")
    assert "SUCCESS" in am_res

    # 4. Grafana CLI check
    graf_res = shell.execute_command("grafana-cli")
    assert "Grafana CLI" in graf_res

    # 5. Kubectl top pods check
    k8s_res = shell.execute_command("kubectl top pods")
    assert "CPU(cores)" in k8s_res

    # 6. Docker stats check
    doc_res = shell.execute_command("docker stats --no-stream")
    assert "prometheus" in doc_res

    # 7. Curl REST API checks
    curl_health = shell.execute_command("curl http://localhost:3000/api/health")
    assert "database" in curl_health

    curl_metrics = shell.execute_command("curl http://localhost:9100/metrics")
    assert "node_cpu_seconds_total" in curl_metrics

    # Cleanup
    runtime = MonitoringRuntime()
    runtime.stop_session("test-mon-123")


def test_monitoring_runtime_lifecycle():
    runtime = MonitoringRuntime()
    res = runtime.create_session("test-mon-lifecycle")
    assert res["container_id"] == "monitoring-test-mon-lifecycle"
    assert res["mode"] == "monitoring"

    session_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../scratch/sessions", "monitoring-test-mon-lifecycle")
    )
    assert os.path.exists(os.path.join(session_dir, "prometheus.yml"))
    assert os.path.exists(os.path.join(session_dir, "alertmanager.yml"))

    runtime.stop_session("test-mon-lifecycle")
    assert not os.path.exists(session_dir)


def test_monitoring_validators():
    runtime = MonitoringRuntime()
    runtime.create_session("test-mon-val")
    shell = MonitoringShell(session_id="test-mon-val")
    
    # Step 1 Check
    val1_before = validation_engine._validate_monitoring(shell, 1, "monitoring-fundamentals")
    assert val1_before["success"] is True

    # Step 2 Check
    shell.execute_command("pwd")
    val2 = validation_engine._validate_monitoring(shell, 2, "monitoring-fundamentals")
    assert val2["success"] is True

    # Step 3 Check
    shell.execute_command("ls -la")
    val3 = validation_engine._validate_monitoring(shell, 3, "monitoring-fundamentals")
    assert val3["success"] is True

    # Step 5 Syntax Check
    shell.execute_command("promtool check config prometheus.yml")
    val5 = validation_engine._validate_monitoring(shell, 5, "prometheus-basics")
    assert val5["success"] is True

    # Step 8 Mini Challenge Check for promql-queries
    shell.execute_command("curl 'http://localhost:9090/api/v1/query?query=rate(process_cpu_seconds_total[5m])'")
    val8 = validation_engine._validate_monitoring(shell, 8, "promql-queries")
    assert val8["success"] is True

    runtime = MonitoringRuntime()
    runtime.stop_session("test-mon-val")
