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
        is_simulated = (mode == "simulated" or (container_id and container_id.startswith("simulated-")))
        
        if is_simulated:
            shell = runtime_service.get_session_shell(session_id)
            if not shell:
                return {"success": False, "message": "Simulated shell session not found."}
                
            if lab_name == "linux-command-line-basics":
                return self._validate_command_line_basics_simulated(shell, task_id)
            elif lab_name == "linux-file-system-permissions":
                return self._validate_file_system_permissions_simulated(shell, task_id)
            elif lab_name == "bash-scripting-fundamentals":
                return self._validate_bash_scripting_simulated(shell, task_id)
            elif lab_name == "linux-networking-processes":
                return self._validate_networking_processes_simulated(shell, task_id)
            elif lab_name == "linux-capstone-project":
                return self._validate_capstone_simulated(shell, task_id)
            elif "docker" in lab_name:
                return self._validate_docker_simulated(shell, task_id)
            else:
                return self._validate_linux_simulated(shell, task_id)
        else:
            if lab_name == "linux-command-line-basics":
                return self._validate_command_line_basics_live(container_id, task_id)
            elif lab_name == "linux-file-system-permissions":
                return self._validate_file_system_permissions_live(container_id, task_id)
            elif lab_name == "bash-scripting-fundamentals":
                return self._validate_bash_scripting_live(container_id, task_id)
            elif lab_name == "linux-networking-processes":
                return self._validate_networking_processes_live(container_id, task_id)
            elif lab_name == "linux-capstone-project":
                return self._validate_capstone_live(container_id, task_id)
            elif "docker" in lab_name:
                return self._validate_docker_live(container_id, task_id)
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



    # ── Command Line Basics ───────────────────────
    def _validate_command_line_basics_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()
        if task_id in [1, 2, 3, 4, 5]:
            cmd_map = {1: "whoami", 2: "pwd", 3: "ls", 4: "ls -a", 5: "ls -l"}
            target = cmd_map[task_id]
            if target in history_str:
                return {"success": True, "message": f"Success! You executed {target} correctly."}
            return {"success": False, "message": f"Try running the '{target}' command."}
        elif task_id == 6:
            if shell.cwd.endswith("drafts"):
                return {"success": True, "message": "Success! You navigated to the drafts directory."}
            return {"success": False, "message": "Navigate to the drafts directory using cd drafts."}
        elif task_id == 7:
            if shell.cwd == "/home/student":
                return {"success": True, "message": "Success! You returned to the home directory."}
            return {"success": False, "message": "Go home using cd ~."}
        elif task_id == 8:
            path = shell.get_local_path("draft.txt")
            if os.path.exists(path) and os.path.isfile(path):
                return {"success": True, "message": "Success! draft.txt created."}
            return {"success": False, "message": "Create draft.txt using touch draft.txt."}
        elif task_id == 9:
            path = shell.get_local_path("projects")
            if os.path.exists(path) and os.path.isdir(path):
                return {"success": True, "message": "Success! projects folder created."}
            return {"success": False, "message": "Create folder projects using mkdir."}
        elif task_id == 10:
            path = shell.get_local_path("draft.txt")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as file:
                    if "hello devlab" in file.read().lower():
                        return {"success": True, "message": "Success! Message written correctly."}
            return {"success": False, "message": "Write 'Hello DevLab' to draft.txt."}
        elif task_id == 11:
            path = shell.get_local_path("draft.txt")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read().lower()
                    if "devops is fun" in content and "hello devlab" in content:
                        return {"success": True, "message": "Success! Text appended."}
            return {"success": False, "message": "Append 'DevOps is fun' to draft.txt."}
        elif task_id == 12:
            if "cat draft.txt" in history_str:
                return {"success": True, "message": "Success! Output printed using cat."}
            return {"success": False, "message": "Use cat draft.txt to view content."}
        elif task_id == 13:
            path = shell.get_local_path("projects/draft_backup.txt")
            if os.path.exists(path):
                return {"success": True, "message": "Success! Copied to backup."}
            return {"success": False, "message": "Copy draft.txt to projects/draft_backup.txt."}
        elif task_id == 14:
            old_path = shell.get_local_path("draft.txt")
            new_path = shell.get_local_path("projects/draft.txt")
            if os.path.exists(new_path) and not os.path.exists(old_path):
                return {"success": True, "message": "Success! File relocated."}
            return {"success": False, "message": "Move draft.txt into projects/ folder."}
        elif task_id == 15:
            path = shell.get_local_path("projects/draft_backup.txt")
            if not os.path.exists(path):
                return {"success": True, "message": "Success! draft_backup.txt removed."}
            return {"success": False, "message": "Remove projects/draft_backup.txt."}
        return {"success": False, "message": "Task not recognized."}

    def _validate_command_line_basics_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
        except Exception as e:
            return {"success": False, "message": f"Docker connection failure: {e}"}
        
        def run_check(cmd: str) -> bool:
            return container.exec_run(cmd, user="student").exit_code == 0

        if task_id in [1, 2, 3, 4, 5, 7, 12]:
            return {"success": True, "message": "Task completed successfully."}
        elif task_id == 6:
            return {"success": True, "message": "Navigated to drafts."}
        elif task_id == 8:
            if run_check("test -f /home/student/draft.txt"):
                return {"success": True, "message": "draft.txt found."}
            return {"success": False, "message": "draft.txt not found."}
        elif task_id == 9:
            if run_check("test -d /home/student/projects"):
                return {"success": True, "message": "projects folder found."}
            return {"success": False, "message": "projects folder not found."}
        elif task_id == 10:
            res = container.exec_run("cat /home/student/draft.txt", user="student")
            if "hello devlab" in res.output.decode().lower():
                return {"success": True, "message": "Text matched."}
            return {"success": False, "message": "Text not matched in draft.txt."}
        elif task_id == 11:
            res = container.exec_run("cat /home/student/draft.txt", user="student")
            if "devops is fun" in res.output.decode().lower():
                return {"success": True, "message": "Appended text matched."}
            return {"success": False, "message": "Appended text not matched."}
        elif task_id == 13:
            if run_check("test -f /home/student/projects/draft_backup.txt"):
                return {"success": True, "message": "backup copy found."}
            return {"success": False, "message": "backup copy not found."}
        elif task_id == 14:
            if run_check("test -f /home/student/projects/draft.txt") and not run_check("test -f /home/student/draft.txt"):
                return {"success": True, "message": "Relocated."}
            return {"success": False, "message": "File not moved correctly."}
        elif task_id == 15:
            if not run_check("test -f /home/student/projects/draft_backup.txt"):
                return {"success": True, "message": "Removed."}
            return {"success": False, "message": "File still exists."}
        return {"success": False, "message": "Task not recognized."}

    # ── File System & Permissions ───────────────────────
    def _validate_file_system_permissions_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()
        if task_id == 1:
            if "ls -l" in history_str:
                return {"success": True, "message": "Success! You printed the detailed list using ls -l."}
            return {"success": False, "message": "Try running the 'ls -l' command."}
        elif task_id == 2:
            path = shell.get_local_path("deploy.sh")
            if os.path.exists(path) and os.path.isfile(path):
                return {"success": True, "message": "Success! deploy.sh created."}
            return {"success": False, "message": "Create deploy.sh using touch deploy.sh."}
        elif task_id == 3:
            if "chmod +x" in history_str or "chmod 755" in history_str or "chmod +x deploy.sh" in history_str:
                return {"success": True, "message": "Success! deploy.sh is now executable."}
            return {"success": False, "message": "Run chmod +x deploy.sh to make it executable."}
        elif task_id == 4:
            path = shell.get_local_path("secrets.txt")
            if os.path.exists(path) and (shell.permissions.get("secrets.txt") == "600" or "chmod 600" in history_str):
                return {"success": True, "message": "Success! secrets.txt created and permissions set to 600."}
            return {"success": False, "message": "Create secrets.txt and set its permissions to 600 using chmod."}
        elif task_id == 5:
            if shell.permissions.get("deploy.sh") == "755" or "chmod 755" in history_str:
                return {"success": True, "message": "Success! deploy.sh permissions updated to 755."}
            return {"success": False, "message": "Change deploy.sh permissions to 755 using chmod."}
        elif task_id == 6:
            if "go-w" in history_str or "chmod 600" in history_str:
                return {"success": True, "message": "Success! Group and others write permission removed."}
            return {"success": False, "message": "Remove write permissions for group and others from secrets.txt using chmod go-w."}
        elif task_id == 7:
            if "ls -l" in history_str:
                return {"success": True, "message": "Success! Checked file ownership."}
            return {"success": False, "message": "List file details using ls -l to check ownership."}
        elif task_id == 8:
            path = shell.get_local_path("private_config")
            if os.path.exists(path) and os.path.isdir(path) and (shell.permissions.get("private_config") == "700" or "chmod 700" in history_str):
                return {"success": True, "message": "Success! private_config folder created and restricted to 700."}
            return {"success": False, "message": "Create folder private_config and set it to 700."}
        return {"success": False, "message": "Task not recognized."}

    def _validate_file_system_permissions_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
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

        def stat_file(path: str) -> str:
            res = container.exec_run(f"stat -c %a {path}", user="student")
            return res.output.decode().strip()

        if task_id in [1, 7]:
            return {"success": True, "message": "Ownership and listing audited successfully."}
        elif task_id == 2:
            if file_exists("/home/student/deploy.sh"):
                return {"success": True, "message": "deploy.sh created."}
            return {"success": False, "message": "deploy.sh not found."}
        elif task_id == 3:
            res = container.exec_run("test -x /home/student/deploy.sh", user="student")
            if res.exit_code == 0:
                return {"success": True, "message": "deploy.sh is executable."}
            return {"success": False, "message": "deploy.sh is not executable."}
        elif task_id == 4:
            if file_exists("/home/student/secrets.txt") and stat_file("/home/student/secrets.txt") == "600":
                return {"success": True, "message": "secrets.txt is set to 600."}
            return {"success": False, "message": "secrets.txt not found or permissions are not 600."}
        elif task_id == 5:
            if stat_file("/home/student/deploy.sh") == "755":
                return {"success": True, "message": "deploy.sh is set to 755."}
            return {"success": False, "message": "deploy.sh permissions are not 755."}
        elif task_id == 6:
            if stat_file("/home/student/secrets.txt") in ["600", "400", "000"]:
                return {"success": True, "message": "secrets.txt group and other write permissions removed."}
            return {"success": False, "message": "secrets.txt still has write permissions for group/others."}
        elif task_id == 8:
            if dir_exists("/home/student/private_config") and stat_file("/home/student/private_config") == "700":
                return {"success": True, "message": "private_config folder set to 700."}
            return {"success": False, "message": "private_config folder not found or permissions are not 700."}
        return {"success": False, "message": "Task not recognized."}

    # ── Bash Scripting Fundamentals ───────────────────────
    def _validate_bash_scripting_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()
        path = shell.get_local_path("hello.sh")
        if task_id == 1:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    if "#!/bin/bash" in f.read():
                        return {"success": True, "message": "Success! hello.sh shebang verified."}
            return {"success": False, "message": "Create hello.sh writing shebang '#!/bin/bash'."}
        elif task_id == 2:
            if "chmod +x" in history_str or "chmod 755" in history_str or "chmod +x hello.sh" in history_str:
                return {"success": True, "message": "Success! hello.sh is now executable."}
            return {"success": False, "message": "Run chmod +x hello.sh to make it executable."}
        elif task_id == 3:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "hello devlab" in content.lower():
                        return {"success": True, "message": "Success! echo command added to hello.sh."}
            return {"success": False, "message": "Append \"echo 'Hello DevLab'\" to hello.sh."}
        elif task_id == 4:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    if "my_name=devopsuser" in f.read().lower():
                        return {"success": True, "message": "Success! MY_NAME variable defined in hello.sh."}
            return {"success": False, "message": "Add variable MY_NAME=DevOpsUser to hello.sh."}
        elif task_id == 5:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "$my_name" in content.lower() or "${my_name}" in content.lower():
                        return {"success": True, "message": "Success! Variable usage verified."}
            return {"success": False, "message": "Add echo referencing $MY_NAME to hello.sh."}
        elif task_id == 6:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "today=" in content.lower() and "date" in content.lower():
                        return {"success": True, "message": "Success! Captured date output in variable."}
            return {"success": False, "message": "Add TODAY=$(date) variable assignment to hello.sh."}
        elif task_id == 7:
            cpath = shell.get_local_path("check.sh")
            if os.path.exists(cpath):
                with open(cpath, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "if " in content and "hello.sh" in content and "fi" in content:
                        return {"success": True, "message": "Success! check.sh conditional script verified."}
            return {"success": False, "message": "Create check.sh with if conditional block checking hello.sh."}
        elif task_id == 8:
            if "for " in history_str and "in" in history_str and "done" in history_str:
                return {"success": True, "message": "Success! for loop execution verified."}
            return {"success": False, "message": "Run a for loop over a b c to echo them."}
        return {"success": False, "message": "Task not recognized."}

    def _validate_bash_scripting_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
        except Exception as e:
            return {"success": False, "message": f"Docker connection failure: {e}"}

        def file_exists(path: str) -> bool:
            res = container.exec_run(f"test -f {path}", user="student")
            return res.exit_code == 0

        def file_contains(path: str, word: str) -> bool:
            res = container.exec_run(f"grep -i '{word}' {path}", user="student")
            return res.exit_code == 0

        if task_id in [2, 8]:
            return {"success": True, "message": "Action verified."}
        elif task_id == 1:
            if file_exists("/home/student/hello.sh") and file_contains("/home/student/hello.sh", "#!/bin/bash"):
                return {"success": True, "message": "hello.sh shebang verified."}
            return {"success": False, "message": "hello.sh shebang not found."}
        elif task_id == 3:
            if file_contains("/home/student/hello.sh", "hello devlab"):
                return {"success": True, "message": "echo command verified."}
            return {"success": False, "message": "hello devlab echo not found in hello.sh."}
        elif task_id == 4:
            if file_contains("/home/student/hello.sh", "my_name="):
                return {"success": True, "message": "Variable definition verified."}
            return {"success": False, "message": "MY_NAME variable not found in hello.sh."}
        elif task_id == 5:
            if file_contains("/home/student/hello.sh", "hello"):
                return {"success": True, "message": "Variable usage verified."}
            return {"success": False, "message": "Variable reference not found in hello.sh."}
        elif task_id == 6:
            if file_contains("/home/student/hello.sh", "today=") and file_contains("/home/student/hello.sh", "date"):
                return {"success": True, "message": "Date capture verified."}
            return {"success": False, "message": "Date variable capture not found in hello.sh."}
        elif task_id == 7:
            if file_exists("/home/student/check.sh") and file_contains("/home/student/check.sh", "if") and file_contains("/home/student/check.sh", "hello.sh"):
                return {"success": True, "message": "check.sh conditional verified."}
            return {"success": False, "message": "check.sh not found or conditional is incorrect."}
        return {"success": False, "message": "Task not recognized."}

    # ── Networking & Processes ───────────────────────
    def _validate_networking_processes_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()
        cmd_map = {
            1: "ps",
            2: "grep",
            3: "ss",
            4: "curl",
            5: "sleep",
            6: "jobs",
            7: "kill",
            8: "ping"
        }
        if task_id in cmd_map:
            target = cmd_map[task_id]
            if target in history_str:
                return {"success": True, "message": f"Success! You executed {target} correctly."}
            return {"success": False, "message": f"Try running the '{target}' utility command."}
        return {"success": False, "message": "Task not recognized."}

    def _validate_networking_processes_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        return {"success": True, "message": "Networking diagnostics completed successfully."}

    # ── Linux Capstone Project ───────────────────────
    def _validate_capstone_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()
        if task_id == 1:
            path_app = shell.get_local_path("devops-project/app")
            path_scr = shell.get_local_path("devops-project/scripts")
            path_log = shell.get_local_path("devops-project/logs")
            path_bak = shell.get_local_path("devops-project/backups")
            if os.path.exists(path_app) and os.path.exists(path_scr) and os.path.exists(path_log) and os.path.exists(path_bak):
                return {"success": True, "message": "Success! Directory structure mapped."}
            return {"success": False, "message": "Create devops-project structure: app, scripts, logs, backups."}
        elif task_id == 2:
            path = shell.get_local_path("devops-project/app/app.env")
            if os.path.exists(path) and (shell.permissions.get("devops-project/app/app.env") == "600" or "chmod 600" in history_str):
                return {"success": True, "message": "Success! app.env created and set to 600."}
            return {"success": False, "message": "Create app.env and chmod 600."}
        elif task_id == 3:
            path = shell.get_local_path("devops-project/scripts/deploy.sh")
            if os.path.exists(path) and (shell.permissions.get("devops-project/scripts/deploy.sh") == "755" or "chmod 755" in history_str or "chmod +x" in history_str):
                return {"success": True, "message": "Success! deploy.sh created and executable."}
            return {"success": False, "message": "Create deploy.sh script and chmod 755."}
        elif task_id == 4:
            path = shell.get_local_path("devops-project/logs/deploy.log")
            if os.path.exists(path) or "deploy.log" in history_str:
                return {"success": True, "message": "Success! Event logged."}
            return {"success": False, "message": "Log event to deploy.log using redirection."}
        elif task_id == 5:
            path = shell.get_local_path("devops-project/backups/app.env.bak")
            if os.path.exists(path):
                return {"success": True, "message": "Success! Configuration backed up."}
            return {"success": False, "message": "Backup app.env as backups/app.env.bak."}
        elif task_id == 6:
            if "ls -la" in history_str or "ls -l" in history_str:
                return {"success": True, "message": "Success! Permissions audited."}
            return {"success": False, "message": "Run ls -la to audit directories."}
        elif task_id == 7:
            if "ss" in history_str:
                return {"success": True, "message": "Success! Listening ports checked."}
            return {"success": False, "message": "Run ss -lntp."}
        elif task_id == 8:
            if "ping" in history_str:
                return {"success": True, "message": "Success! Connectivity checked."}
            return {"success": False, "message": "Run ping."}
        elif task_id == 9:
            path = shell.get_local_path("devops-project/scripts/healthcheck.sh")
            if os.path.exists(path):
                return {"success": True, "message": "Success! healthcheck.sh created."}
            return {"success": False, "message": "Create healthcheck.sh in scripts/."}
        elif task_id == 10:
            if "ls -lar" in history_str or "ls -la" in history_str:
                return {"success": True, "message": "Success! Final project checked."}
            return {"success": False, "message": "Run recursive ls -laR check."}
        return {"success": False, "message": "Task not recognized."}

    def _validate_capstone_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
        except Exception as e:
            return {"success": False, "message": f"Docker connection failure: {e}"}

        def run_check(cmd: str) -> bool:
            return container.exec_run(cmd, user="student").exit_code == 0

        def stat_file(path: str) -> str:
            res = container.exec_run(f"stat -c %a {path}", user="student")
            return res.output.decode().strip()

        if task_id in [6, 7, 8, 10]:
            return {"success": True, "message": "Capstone health checklist passed."}
        elif task_id == 1:
            if run_check("test -d /home/student/devops-project/app -a -d /home/student/devops-project/scripts -a -d /home/student/devops-project/logs"):
                return {"success": True, "message": "Directory structure exists."}
            return {"success": False, "message": "devops-project directory structure not found."}
        elif task_id == 2:
            if run_check("test -f /home/student/devops-project/app/app.env") and stat_file("/home/student/devops-project/app/app.env") == "600":
                return {"success": True, "message": "app.env exists with mode 600."}
            return {"success": False, "message": "app.env not found or permissions are not 600."}
        elif task_id == 3:
            if run_check("test -f /home/student/devops-project/scripts/deploy.sh") and run_check("test -x /home/student/devops-project/scripts/deploy.sh"):
                return {"success": True, "message": "deploy.sh exists and is executable."}
            return {"success": False, "message": "deploy.sh not found or not executable."}
        elif task_id == 4:
            if run_check("test -f /home/student/devops-project/logs/deploy.log"):
                return {"success": True, "message": "deploy.log found."}
            return {"success": False, "message": "deploy.log not found."}
        elif task_id == 5:
            if run_check("test -f /home/student/devops-project/backups/app.env.bak"):
                return {"success": True, "message": "app.env.bak backup found."}
            return {"success": False, "message": "app.env.bak backup not found."}
        elif task_id == 9:
            if run_check("test -f /home/student/devops-project/scripts/healthcheck.sh") and run_check("test -x /home/student/devops-project/scripts/healthcheck.sh"):
                return {"success": True, "message": "healthcheck.sh exists and is executable."}
            return {"success": False, "message": "healthcheck.sh not found or not executable."}
        return {"success": False, "message": "Task not recognized."}


validation_engine = ValidationEngine()
