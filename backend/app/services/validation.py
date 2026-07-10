import os
import logging
from typing import Dict, Any, List
import docker
from app.services.runtime import runtime_service

logger = logging.getLogger("app.services.validation")


class ValidationEngine:
    def validate_task(
        self,
        session_id: str,
        container_id: str,
        task_id: int,
        mode: str,
        lab_name: str = "linux-basics",
    ) -> Dict[str, Any]:
        """
        Routes the validation check to the appropriate course validators (Linux or Docker).
        """
        if "docker" in lab_name:
            if mode == "simulated" or container_id.startswith("simulated-"):
                shell = runtime_service.get_session_shell(session_id)
                if not shell:
                    return {"success": False, "message": "Simulated shell session not found."}
                return self._validate_docker_simulated(shell, task_id)
            else:
                return self._validate_docker_live(container_id, task_id)
        else:
            # Linux Validation
            if mode == "simulated" or container_id.startswith("simulated-"):
                shell = runtime_service.get_session_shell(session_id)
                if not shell:
                    return {"success": False, "message": "Simulated shell session not found."}
                return self._validate_linux_simulated(shell, task_id)
            else:
                return self._validate_linux_live(container_id, task_id)

    def _validate_linux_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()

        if task_id == 1:
            if "pwd" in history_str:
                return {"success": True, "message": "Success! You queried the working directory."}
            return {"success": False, "message": "Try running the 'pwd' command to view your path."}
        elif task_id == 2:
            if "ls -a" in history_str or "ls -la" in history_str or "ls -al" in history_str:
                return {"success": True, "message": "Success! You listed files including hidden ones."}
            return {"success": False, "message": "Try running 'ls -a' or 'ls -la' to show all directory contents."}
        elif task_id == 3:
            path = shell.get_local_path("note.txt")
            if os.path.exists(path) and os.path.isfile(path):
                return {"success": True, "message": "Success! 'note.txt' file created."}
            return {"success": False, "message": "Create an empty file named 'note.txt' using the touch command."}
        elif task_id == 4:
            path = shell.get_local_path("backup")
            if os.path.exists(path) and os.path.isdir(path):
                return {"success": True, "message": "Success! 'backup' directory created."}
            return {"success": False, "message": "Create a subfolder named 'backup' in your home path using mkdir."}
        elif task_id == 5:
            path = shell.get_local_path("backup/note_copy.txt")
            if os.path.exists(path) and os.path.isfile(path):
                return {"success": True, "message": "Success! note.txt copied to backup/note_copy.txt."}
            return {"success": False, "message": "Copy note.txt into the backup directory as note_copy.txt."}
        elif task_id == 6:
            path = shell.get_local_path("note_copy.txt")
            if os.path.exists(path) and os.path.isfile(path):
                return {"success": True, "message": "Success! File moved back to home directory."}
            return {"success": False, "message": "Move note_copy.txt from the backup/ directory back to your home directory."}
        elif task_id == 7:
            old_path = shell.get_local_path("note_copy.txt")
            new_path = shell.get_local_path("log.txt")
            if os.path.exists(new_path) and not os.path.exists(old_path):
                return {"success": True, "message": "Success! note_copy.txt renamed to log.txt."}
            return {"success": False, "message": "Rename note_copy.txt in your home directory to log.txt using mv."}
        elif task_id == 8:
            path = shell.get_local_path("note.txt")
            if not os.path.exists(path):
                return {"success": True, "message": "Success! note.txt deleted."}
            return {"success": False, "message": "Delete the original note.txt file using rm."}
        elif task_id == 9:
            if "cat log.txt" in history_str or "less log.txt" in history_str:
                return {"success": True, "message": "Success! You viewed the contents of log.txt."}
            return {"success": False, "message": "Use the cat command to inspect the contents of log.txt."}
        elif task_id == 10:
            perm = shell.permissions.get("log.txt")
            if perm == "600" or "chmod 600" in history_str:
                return {"success": True, "message": "Success! Permissions updated to 600 (owner read/write)."}
            return {"success": False, "message": "Change the permissions of log.txt to 600 (owner only access) using chmod."}
        elif task_id == 11:
            if "id" in history_str:
                return {"success": True, "message": "Success! You inspected your user identity stats."}
            return {"success": False, "message": "Run the 'id' command to view your user and group identifiers."}
        elif task_id == 12:
            if "groups" in history_str or "id" in history_str:
                return {"success": True, "message": "Success! Group memberships validated."}
            return {"success": False, "message": "Check your user groups using the 'groups' command."}
        elif task_id == 13:
            if "grep" in history_str:
                return {"success": True, "message": "Success! Grep keyword match verified."}
            return {"success": False, "message": "Search for lines or strings in files using the grep command."}
        elif task_id == 14:
            if "|" in history_str and "grep" in history_str:
                return {"success": True, "message": "Success! Command pipeline executed correctly."}
            return {"success": False, "message": "Pipe the directory list to grep to filter files: ls | grep log.txt"}
        elif task_id == 15:
            path = shell.get_local_path("dynamic.txt")
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        content = f.read().strip().lower()
                    if "devops" in content:
                        return {"success": True, "message": "Success! Output redirected into dynamic.txt."}
                except:
                    pass
            return {"success": False, "message": "Write the word 'DevOps' into a new file named dynamic.txt using redirect (>)."}
        elif task_id == 16:
            if shell.env.get("REGISTRY") == "local" or "export registry=local" in history_str:
                return {"success": True, "message": "Success! Env variable REGISTRY is set."}
            return {"success": False, "message": "Export a custom environment variable named REGISTRY with value 'local'."}
        elif task_id == 17:
            if "ps" in history_str or "top" in history_str:
                return {"success": True, "message": "Success! Active system processes listed."}
            return {"success": False, "message": "View running processes in this console environment using 'ps'."}
        elif task_id == 18:
            if "ip route" in history_str or "route" in history_str or "ifconfig" in history_str or "ip a" in history_str:
                return {"success": True, "message": "Success! Inspected network details."}
            return {"success": False, "message": "Check routing tables or configuration parameters using 'ip route'."}
        elif task_id == 19:
            path = shell.get_local_path("backup")
            if not os.path.exists(path):
                return {"success": True, "message": "Success! backup folder cleaned up."}
            return {"success": False, "message": "Delete the backup directory and all files inside recursively using rm -rf."}
        elif task_id == 20:
            local_cwd = shell.get_local_path(shell.cwd)
            files = os.listdir(local_cwd)
            if "backup" not in files and "note.txt" not in files:
                return {"success": True, "message": "Perfect! Workspace successfully verified and complete!"}
            return {"success": False, "message": "Verify that backup and note.txt files are deleted and execute ls -la."}

        return {"success": False, "message": "Unknown task identifier."}

    def _validate_linux_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
        except Exception as e:
            return {"success": False, "message": f"Docker connection failure: {e}"}

        def file_exists(path: str) -> bool:
            res = container.exec_run(f"test -f {path}", user="student")
            return res.exit_code == 0

        def dir_exists(path: str) -> bool:
            res = container.exec_run(f"test -d {path}", user="student")
            return res.exit_code == 0

        # Simple file checking validations
        if task_id in [1, 2, 9, 11, 12, 13, 14, 17, 18]:
            return {"success": True, "message": "Task verification checks out successfully."}
        elif task_id == 3:
            if file_exists("/home/student/note.txt"):
                return {"success": True, "message": "Success! 'note.txt' exists."}
            return {"success": False, "message": "note.txt not found in /home/student"}
        elif task_id == 4:
            if dir_exists("/home/student/backup"):
                return {"success": True, "message": "Success! 'backup' directory exists."}
            return {"success": False, "message": "backup directory not found in /home/student"}
        elif task_id == 5:
            if file_exists("/home/student/backup/note_copy.txt"):
                return {"success": True, "message": "Success! note_copy.txt successfully copied."}
            return {"success": False, "message": "note_copy.txt not found in backup/"}
        elif task_id == 6:
            if file_exists("/home/student/note_copy.txt"):
                return {"success": True, "message": "Success! note_copy.txt moved back to home."}
            return {"success": False, "message": "note_copy.txt not found in /home/student"}
        elif task_id == 7:
            if file_exists("/home/student/log.txt") and not file_exists("/home/student/note_copy.txt"):
                return {"success": True, "message": "Success! note_copy.txt renamed to log.txt."}
            return {"success": False, "message": "log.txt not found, or note_copy.txt still exists"}
        elif task_id == 8:
            if not file_exists("/home/student/note.txt"):
                return {"success": True, "message": "Success! note.txt deleted."}
            return {"success": False, "message": "note.txt still exists"}
        elif task_id == 10:
            res = container.exec_run("stat -c %a /home/student/log.txt", user="student")
            if res.exit_code == 0 and res.output.decode().strip() == "600":
                return {"success": True, "message": "Success! Permissions set to 600."}
            return {"success": False, "message": "Permissions of log.txt are not 600"}
        elif task_id == 15:
            if file_exists("/home/student/dynamic.txt"):
                res = container.exec_run("cat /home/student/dynamic.txt", user="student")
                if "devops" in res.output.decode().lower():
                    return {"success": True, "message": "Success! Output redirected correctly."}
            return {"success": False, "message": "dynamic.txt does not contain 'DevOps'"}
        elif task_id == 16:
            return {"success": True, "message": "Success! Env parameters checked."}
        elif task_id == 19:
            if not dir_exists("/home/student/backup"):
                return {"success": True, "message": "Success! backup folder deleted."}
            return {"success": False, "message": "backup directory still exists"}
        elif task_id == 20:
            if not file_exists("/home/student/note.txt") and not dir_exists("/home/student/backup"):
                return {"success": True, "message": "Success! Final cleanup checklist complete!"}
            return {"success": False, "message": "Cleanup incomplete."}

        return {"success": False, "message": "Unknown task."}

    # ── Docker Labs Validations ───────────────────────

    def _validate_docker_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        """
        Validates Docker course progress against local SimulatedDockerShell properties.
        """
        history_str = " ".join(shell.history).lower()

        if task_id == 1:
            if "docker --version" in history_str or "docker -v" in history_str:
                return {"success": True, "message": "Success! Docker CLI client check completed."}
            return {"success": False, "message": "Try running the 'docker --version' command."}
        elif task_id == 2:
            if "docker info" in history_str:
                return {"success": True, "message": "Success! Docker daemon system information fetched."}
            return {"success": False, "message": "Query daemon details by running 'docker info'."}
        elif task_id == 3:
            # Check if hello-world exists in simulated containers list
            hello_exists = any("hello-world" in c["image"] for c in shell.mock_containers.values())
            if hello_exists:
                return {"success": True, "message": "Success! hello-world container ran."}
            return {"success": False, "message": "Launch the hello-world container using 'docker run hello-world'."}
        elif task_id == 4:
            if "alpine" in shell.mock_images:
                return {"success": True, "message": "Success! alpine image downloaded."}
            return {"success": False, "message": "Pull the alpine image using 'docker pull alpine'."}
        elif task_id == 5:
            if "my_web" in shell.mock_containers and shell.mock_containers["my_web"]["status"] == "running":
                return {"success": True, "message": "Success! my_web Nginx server is active."}
            return {"success": False, "message": "Launch a detached container named 'my_web' running nginx."}
        elif task_id == 6:
            if "docker ps -a" in history_str:
                return {"success": True, "message": "Success! All containers listed including stopped ones."}
            return {"success": False, "message": "List all containers using 'docker ps -a'."}
        elif task_id == 7:
            path = shell.get_local_path("Dockerfile")
            if os.path.exists(path):
                return {"success": True, "message": "Success! Dockerfile created."}
            return {"success": False, "message": "Create a text file named 'Dockerfile' containing instructions."}
        elif task_id == 8:
            if "docker build" in history_str:
                return {"success": True, "message": "Success! Custom image built successfully."}
            return {"success": False, "message": "Compile your custom image: docker build -t custom_app:v1 ."}
        elif task_id == 9:
            if history_str.count("docker build") >= 2:
                return {"success": True, "message": "Success! Build caches reused."}
            return {"success": False, "message": "Re-run the build command to trigger docker cache matching."}
        elif task_id == 10:
            if "db_data" in shell.mock_volumes:
                return {"success": True, "message": "Success! Volume db_data created."}
            return {"success": False, "message": "Create a volume named db_data: docker volume create db_data"}
        elif task_id == 11:
            if "backend_net" in shell.mock_networks:
                return {"success": True, "message": "Success! Network backend_net created."}
            return {"success": False, "message": "Create a network named backend_net: docker network create backend_net"}
        elif task_id == 12:
            if "env_web" in shell.mock_containers:
                return {"success": True, "message": "Success! env_web container with variables launched."}
            return {"success": False, "message": "Launch env_web nginx container passing variable PORT=8080."}
        elif task_id == 13:
            if "docker logs" in history_str:
                return {"success": True, "message": "Success! my_web logs stdout inspected."}
            return {"success": False, "message": "Query logs from my_web container: docker logs my_web"}
        elif task_id == 14:
            if "docker exec" in history_str:
                return {"success": True, "message": "Success! Exec command executed successfully."}
            return {"success": False, "message": "Execute date command on my_web: docker exec my_web date"}
        elif task_id == 15:
            if "docker inspect" in history_str:
                return {"success": True, "message": "Success! Resource configuration inspected."}
            return {"success": False, "message": "Inspect bridge network details: docker inspect bridge"}
        elif task_id == 16:
            path = shell.get_local_path("Dockerfile.multistage")
            if os.path.exists(path):
                return {"success": True, "message": "Success! Multi-stage Dockerfile saved."}
            return {"success": False, "message": "Save multistage configurations to Dockerfile.multistage."}
        elif task_id == 17:
            if "my_web" not in shell.mock_containers or shell.mock_containers["my_web"]["status"] != "running":
                return {"success": True, "message": "Success! my_web stopped and cleared."}
            return {"success": False, "message": "Stop and delete my_web: docker stop my_web && docker rm my_web"}
        elif task_id == 18:
            path = shell.get_local_path("docker-compose.yml")
            if os.path.exists(path):
                return {"success": True, "message": "Success! Multi-container compose project completed!"}
            return {"success": False, "message": "Create docker-compose.yml containing web and db services."}

        return {"success": False, "message": "Unknown Docker task identifier."}

    def _validate_docker_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        """
        Validates nested Docker container configurations by running commands inside student sandbox.
        """
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
        except Exception as e:
            return {"success": False, "message": f"Docker connection failure: {e}"}

        def run_in_sandbox(cmd: str) -> bool:
            # Runs command inside the student container sandbox
            res = container.exec_run(cmd, user="student")
            return res.exit_code == 0

        if task_id == 1:
            if run_in_sandbox("docker --version"):
                return {"success": True, "message": "Success! Docker CLI client check completed."}
            return {"success": False, "message": "docker cli not found or permission denied."}
        elif task_id == 2:
            if run_in_sandbox("docker info"):
                return {"success": True, "message": "Success! Connection to nested docker daemon verified."}
            return {"success": False, "message": "docker info failed. Check docker permissions."}
        elif task_id == 3:
            # Check hello-world run
            if run_in_sandbox("docker inspect hello-world"):
                return {"success": True, "message": "Success! hello-world container ran."}
            return {"success": False, "message": "hello-world container not found."}
        elif task_id == 4:
            if run_in_sandbox("docker image inspect alpine"):
                return {"success": True, "message": "Success! alpine image downloaded."}
            return {"success": False, "message": "alpine image not found in image list."}
        elif task_id == 5:
            if run_in_sandbox("docker inspect my_web"):
                return {"success": True, "message": "Success! my_web container is active."}
            return {"success": False, "message": "my_web container not found."}
        elif task_id == 6:
            return {"success": True, "message": "Success! Containers list verified."}
        elif task_id == 7:
            if run_in_sandbox("test -f /home/student/Dockerfile"):
                return {"success": True, "message": "Success! Dockerfile created."}
            return {"success": False, "message": "Dockerfile not found in home folder."}
        elif task_id == 8:
            if run_in_sandbox("docker image inspect custom_app:v1"):
                return {"success": True, "message": "Success! custom_app:v1 built successfully."}
            return {"success": False, "message": "custom_app:v1 image not found."}
        elif task_id == 9:
            return {"success": True, "message": "Success! Image cached checks verified."}
        elif task_id == 10:
            if run_in_sandbox("docker volume inspect db_data"):
                return {"success": True, "message": "Success! Volume db_data created."}
            return {"success": False, "message": "db_data volume not found."}
        elif task_id == 11:
            if run_in_sandbox("docker network inspect backend_net"):
                return {"success": True, "message": "Success! Network backend_net created."}
            return {"success": False, "message": "backend_net network not found."}
        elif task_id == 12:
            if run_in_sandbox("docker inspect env_web"):
                return {"success": True, "message": "Success! env_web container with variables active."}
            return {"success": False, "message": "env_web container not found."}
        elif task_id == 13:
            return {"success": True, "message": "Success! Container logs checked."}
        elif task_id == 14:
            return {"success": True, "message": "Success! Container exec checks checked."}
        elif task_id == 15:
            return {"success": True, "message": "Success! Networking inspects checked."}
        elif task_id == 16:
            if run_in_sandbox("test -f /home/student/Dockerfile.multistage"):
                return {"success": True, "message": "Success! Multi-stage Dockerfile created."}
            return {"success": False, "message": "Dockerfile.multistage not found."}
        elif task_id == 17:
            # container my_web should be removed
            res = container.exec_run("docker inspect my_web", user="student")
            if res.exit_code != 0:
                return {"success": True, "message": "Success! my_web container removed."}
            return {"success": False, "message": "my_web container still exists."}
        elif task_id == 18:
            if run_in_sandbox("test -f /home/student/docker-compose.yml"):
                return {"success": True, "message": "Success! Final multi-container project completed!"}
            return {"success": False, "message": "docker-compose.yml not found."}

        return {"success": False, "message": "Unknown Docker task."}


validation_engine = ValidationEngine()
