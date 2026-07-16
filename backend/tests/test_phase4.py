import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.redis import redis_client, UpstashRedisClient
from app.courses.engine import course_engine
from app.services.runtime import LinuxRuntime, DockerRuntime, runtime_service
from app.services.validation import validation_engine

client = TestClient(app)


def test_redis_client_fallback():
    """
    Tests that UpstashRedisClient reads, writes, and handles expiries/increments.
    """
    client_test = UpstashRedisClient()
    # Test setting and getting keys (with fallback if Upstash config is inactive)
    client_test.set("test_key", "test_val", ex=10)
    assert client_test.get("test_key") == "test_val"

    # Test deletions
    client_test.delete("test_key")
    assert client_test.get("test_key") is None

    # Test increments
    client_test.set("test_counter", 5)
    new_val = client_test.incr("test_counter")
    assert new_val == 6
    assert client_test.get("test_counter") == "6"


def test_course_engine():
    """
    Verifies that course_engine loads syllabus lists and lesson objectives from files dynamically.
    """
    linux_lessons = course_engine.get_lessons("linux-basics")
    assert len(linux_lessons) == 20
    assert linux_lessons[0]["id"] == 1
    assert "pwd" in linux_lessons[0]["title"].lower()

    docker_lessons = course_engine.get_lessons("docker-basics")
    assert len(docker_lessons) == 18
    assert docker_lessons[0]["id"] == 1
    assert "introduction" in docker_lessons[0]["title"].lower()

    metadata = course_engine.get_course_metadata("docker-basics")
    assert metadata["total_lessons"] == 18
    assert metadata["difficulty"] == "Intermediate"


def test_runtimes_instantiation():
    """
    Verifies that Linux and Docker runtime drivers configure container specifications.
    """
    linux_driver = LinuxRuntime(docker_client=None)
    docker_driver = DockerRuntime(docker_client=None)

    # Simulated bootstrap fallbacks
    linux_res = linux_driver.create_session("session123")
    assert linux_res["mode"] == "simulated"
    assert linux_res["container_id"] == "simulated-session123"

    docker_res = docker_driver.create_session("session123")
    assert docker_res["mode"] == "simulated"
    assert docker_res["container_id"] == "simulated-session123"


def test_validation_engine_routing():
    """
    Verifies that validation routing evaluates student answers correctly.
    """
    # Initialize a simulated sandbox coordinator for tests
    runtime_service.create_lab("test_sess", lab_name="linux-basics")
    shell = runtime_service.get_session_shell("test_sess")
    assert shell is not None

    # Add pwd to history to pass check 1
    shell.execute_command("pwd")
    res = validation_engine.validate_task(
        session_id="test_sess",
        container_id="simulated-test_sess",
        task_id=1,
        mode="simulated",
        lab_name="linux-basics"
    )
    assert res["success"] is True

    # Docker lab checks
    runtime_service.create_lab("test_dock_sess", lab_name="docker-basics")
    docker_shell = runtime_service.get_session_shell("test_dock_sess")
    assert docker_shell is not None

    docker_shell.execute_command("docker --version")
    dock_res = validation_engine.validate_task(
        session_id="test_dock_sess",
        container_id="simulated-test_dock_sess",
        task_id=1,
        mode="simulated",
        lab_name="docker-basics"
    )
    assert dock_res["success"] is True

    # Clean up mock directories
    runtime_service.stop_lab("test_sess", "simulated-test_sess", "linux-basics")
    runtime_service.stop_lab("test_dock_sess", "simulated-test_dock_sess", "docker-basics")


def test_rate_limiting_middleware_trigger():
    """
    Tests that rate limiting triggers and responds with 429 when limits are breached.
    """
    # Temporarily set rate limit key for test IP
    test_ip = "127.0.0.1"
    import time
    timestamp = int(time.time() // 60)
    
    # Pre-seed the count to exceed 100 requests limit for previous, current and next minute to avoid clock race
    for offset in [-1, 0, 1]:
        redis_client.set(f"ratelimit:{test_ip}:{timestamp + offset}", 101)
        redis_client.set(f"ratelimit:testclient:{timestamp + offset}", 101)
    
    # Requesting the API route should return 429
    res = client.get("/api/v1/labs")
    assert res.status_code == 429
    assert "rate limit exceeded" in res.json()["detail"].lower()

    # Clean up limit counters
    for offset in [-1, 0, 1]:
        redis_client.delete(f"ratelimit:{test_ip}:{timestamp + offset}")
        redis_client.delete(f"ratelimit:testclient:{timestamp + offset}")
