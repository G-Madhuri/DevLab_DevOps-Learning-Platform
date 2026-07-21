import pytest
import os
import json
from app.services.runtime import ObservabilityShell, ObservabilityRuntime
from app.services.validation import validation_engine

def test_observability_shell_commands():
    shell = ObservabilityShell(session_id="test-obs-123")
    
    # 1. Whitelist validation
    unallowed = shell.execute_command("unauthorized_tool --hack")
    assert "command not allowed" in unallowed

    # 2. Otelcol validate check
    otel_res = shell.execute_command("otelcol validate --config otel-collector.yaml")
    assert "SUCCESS" in otel_res

    # 3. Logcli query check
    log_res = shell.execute_command("logcli query '{job=\"varlogs\"}'")
    assert "trace_id" in log_res

    # 4. Kubectl logs check
    k8s_res = shell.execute_command("kubectl logs deploy/web-app")
    assert "trace_id" in k8s_res

    # 5. Grep check
    grep_res = shell.execute_command("grep ERROR app.log")
    assert "ConnectionRefusedError" in grep_res

    # 6. Curl REST API checks
    curl_elk = shell.execute_command("curl http://localhost:9200/_cluster/health")
    assert "devlab-elk" in curl_elk

    curl_jaeger = shell.execute_command("curl http://localhost:16686/api/services")
    assert "checkoutservice" in curl_jaeger

    # Cleanup
    runtime = ObservabilityRuntime()
    runtime.stop_session("test-obs-123")


def test_observability_runtime_lifecycle():
    runtime = ObservabilityRuntime()
    res = runtime.create_session("test-obs-lifecycle")
    assert res["container_id"] == "observability-test-obs-lifecycle"
    assert res["mode"] == "observability"

    session_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../scratch/sessions", "observability-test-obs-lifecycle")
    )
    assert os.path.exists(os.path.join(session_dir, "otel-collector.yaml"))
    assert os.path.exists(os.path.join(session_dir, "app.log"))

    runtime.stop_session("test-obs-lifecycle")
    assert not os.path.exists(session_dir)


def test_observability_validators():
    runtime = ObservabilityRuntime()
    runtime.create_session("test-obs-val")
    shell = ObservabilityShell(session_id="test-obs-val")
    
    # Step 1 Check
    val1 = validation_engine._validate_observability(shell, 1, "observability-fundamentals")
    assert val1["success"] is True

    # Step 2 Check
    shell.execute_command("pwd")
    val2 = validation_engine._validate_observability(shell, 2, "observability-fundamentals")
    assert val2["success"] is True

    # Step 3 Check
    shell.execute_command("ls -la")
    val3 = validation_engine._validate_observability(shell, 3, "observability-fundamentals")
    assert val3["success"] is True

    # Step 5 Syntax Check
    shell.execute_command("otelcol validate --config otel-collector.yaml")
    val5 = validation_engine._validate_observability(shell, 5, "opentelemetry-fundamentals")
    assert val5["success"] is True

    # Step 8 Mini Challenge Check for distributed-tracing-with-jaeger
    shell.execute_command("curl http://localhost:16686/api/services")
    val8 = validation_engine._validate_observability(shell, 8, "distributed-tracing-with-jaeger")
    assert val8["success"] is True

    runtime.stop_session("test-obs-val")
