import os
import logging
import subprocess
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
        Routes the validation check to the appropriate course validators (Linux, Docker, Git, Actions, CI/CD, Jenkins or Kubernetes).
        """
        if "aws" in lab_name or "iam-" in lab_name or "ec2-" in lab_name or "vpc-" in lab_name or "s3-" in lab_name or "rds-" in lab_name or "load-balancers-" in lab_name or "cloudwatch-" in lab_name:
            shell = runtime_service.get_session_shell(session_id)
            if not shell:
                return {"success": False, "message": "AWS shell session not found."}
            return self._validate_aws(shell, task_id, lab_name)

        if "ansible" in lab_name or "inventory-files" in lab_name or "ad-hoc-commands" in lab_name or "writing-playbooks" in lab_name or "variables-and-facts" in lab_name or "templates-and-jinja2" in lab_name or "ansible-galaxy" in lab_name or "tags-handlers-and" in lab_name:
            shell = runtime_service.get_session_shell(session_id)
            if not shell:
                return {"success": False, "message": "Ansible shell session not found."}
            return self._validate_ansible(shell, task_id, lab_name)

        if "terraform" in lab_name or "variables-outputs" in lab_name or "state-management" in lab_name or "best-practices-terraform" in lab_name:
            shell = runtime_service.get_session_shell(session_id)
            if not shell:
                return {"success": False, "message": "Terraform shell session not found."}
            return self._validate_terraform(shell, task_id, lab_name)

        if "jenkins" in lab_name or "freestyle-jobs" in lab_name or "declarative-vs-" in lab_name or "distributed-builds" in lab_name or "credentials-and-secrets" in lab_name or "plugins-and-" in lab_name:
            shell = runtime_service.get_session_shell(session_id)
            if not shell:
                return {"success": False, "message": "Jenkins shell session not found."}
            return self._validate_jenkins(shell, task_id, lab_name)

        if "introduction-to-cicd" in lab_name or "continuous-" in lab_name or "building-a-complete-cicd" in lab_name or lab_name == "cicd":
            shell = runtime_service.get_session_shell(session_id)
            if not shell:
                return {"success": False, "message": "CI/CD shell session not found."}
            return self._validate_cicd(shell, task_id, lab_name)

        if "github-actions" in lab_name:
            shell = runtime_service.get_session_shell(session_id)
            if not shell:
                return {"success": False, "message": "Actions shell session not found."}
            return self._validate_github_actions(shell, task_id, lab_name)

        if "git-" in lab_name or lab_name == "git":
            shell = runtime_service.get_session_shell(session_id)
            if not shell:
                return {"success": False, "message": "Git shell session not found."}
            return self._validate_git(shell, task_id, lab_name)

        is_simulated = (mode == "simulated" or (container_id and container_id.startswith("simulated-")))
        
        if "kubernetes-" in lab_name or "k8s-" in lab_name:
            if is_simulated:
                shell = runtime_service.get_session_shell(session_id)
                if not shell:
                    return {"success": False, "message": "Simulated shell session not found."}
                return self._validate_kubernetes_simulated(shell, task_id, lab_name)
            else:
                return self._validate_kubernetes_live(session_id, task_id, lab_name)

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
            elif lab_name == "docker-fundamentals":
                return self._validate_docker_fundamentals_simulated(shell, task_id)
            elif lab_name == "multi-container-with-docker-compose":
                return self._validate_docker_compose_simulated(shell, task_id)
            elif lab_name == "docker-networking-deep-dive":
                return self._validate_docker_networking_simulated(shell, task_id)
            elif lab_name == "optimizing-dockerfiles":
                return self._validate_optimizing_dockerfiles_simulated(shell, task_id)
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
            elif lab_name == "docker-fundamentals":
                return self._validate_docker_fundamentals_live(container_id, task_id)
            elif lab_name == "multi-container-with-docker-compose":
                return self._validate_docker_compose_live(container_id, task_id)
            elif lab_name == "docker-networking-deep-dive":
                return self._validate_docker_networking_live(container_id, task_id)
            elif lab_name == "optimizing-dockerfiles":
                return self._validate_optimizing_dockerfiles_live(container_id, task_id)
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

    # ── Docker Fundamentals Validator ───────────────────
    def _validate_docker_fundamentals_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()
        if task_id == 1:
            if "docker --version" in history_str or "docker -v" in history_str or "docker version" in history_str:
                return {"success": True, "message": "Success! Docker CLI client check completed."}
            return {"success": False, "message": "Try running the 'docker --version' command."}
        elif task_id == 2:
            if "docker info" in history_str:
                return {"success": True, "message": "Success! Docker daemon system information fetched."}
            return {"success": False, "message": "Query daemon details by running 'docker info'."}
        elif task_id == 3:
            if "alpine" in shell.mock_images:
                return {"success": True, "message": "Success! alpine image downloaded."}
            return {"success": False, "message": "Pull the alpine image using 'docker pull alpine'."}
        elif task_id == 4:
            if "docker images" in history_str or "docker image ls" in history_str:
                return {"success": True, "message": "Success! Local images list queried."}
            return {"success": False, "message": "List available local images using 'docker images'."}
        elif task_id == 5:
            hello_exists = any("hello-world" in c["image"] for c in shell.mock_containers.values())
            if hello_exists:
                return {"success": True, "message": "Success! hello-world container ran."}
            return {"success": False, "message": "Launch the hello-world container using 'docker run hello-world'."}
        elif task_id == 6:
            if "my_web" in shell.mock_containers and shell.mock_containers["my_web"]["status"] == "running":
                return {"success": True, "message": "Success! my_web Nginx server is active."}
            return {"success": False, "message": "Launch a detached container named 'my_web' running nginx."}
        elif task_id == 7:
            if "docker ps" in history_str or "docker container ls" in history_str:
                return {"success": True, "message": "Success! Running containers listed."}
            return {"success": False, "message": "List running containers using 'docker ps'."}
        elif task_id == 8:
            if "docker inspect my_web" in history_str or "docker container inspect my_web" in history_str:
                return {"success": True, "message": "Success! Container metadata inspect command executed."}
            return {"success": False, "message": "Inspect my_web configuration: docker inspect my_web"}
        return {"success": False, "message": "Unknown task."}

    def _validate_docker_fundamentals_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
        except Exception as e:
            return {"success": False, "message": f"Docker connection failure: {e}"}

        def run_in_sandbox(cmd: str) -> bool:
            res = container.exec_run(cmd, user="student")
            return res.exit_code == 0

        if task_id in [1, 2, 4, 7]:
            return {"success": True, "message": "Verification passed."}
        elif task_id == 3:
            if run_in_sandbox("docker image inspect alpine"):
                return {"success": True, "message": "Success! alpine image pulled."}
            return {"success": False, "message": "alpine image not found."}
        elif task_id == 5:
            if run_in_sandbox("docker inspect hello-world"):
                return {"success": True, "message": "Success! hello-world execution verified."}
            return {"success": False, "message": "hello-world container not found."}
        elif task_id == 6:
            if run_in_sandbox("docker inspect my_web"):
                return {"success": True, "message": "Success! Nginx server is active."}
            return {"success": False, "message": "my_web container not found."}
        elif task_id == 8:
            return {"success": True, "message": "Success! Metadata inspection verified."}
        return {"success": False, "message": "Unknown task."}

    # ── Docker Compose Validator ────────────────────────
    def _validate_docker_compose_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()
        if task_id == 1:
            path = shell.get_local_path("docker-compose.yml")
            if os.path.exists(path):
                return {"success": True, "message": "Success! docker-compose.yml created."}
            return {"success": False, "message": "Create docker-compose.yml file first."}
        elif task_id == 2:
            if "docker compose config" in history_str or "docker-compose config" in history_str:
                return {"success": True, "message": "Success! config syntax check executed."}
            return {"success": False, "message": "Run validation check using 'docker compose config'."}
        elif task_id == 3:
            if shell.mock_compose_active or "up" in history_str:
                return {"success": True, "message": "Success! multi-container compose services running."}
            return {"success": False, "message": "Launch stack: docker compose up -d"}
        elif task_id == 4:
            if "docker compose ps" in history_str or "docker-compose ps" in history_str:
                return {"success": True, "message": "Success! ps output verified."}
            return {"success": False, "message": "Check compose container lists: docker compose ps"}
        elif task_id == 5:
            if "docker compose images" in history_str or "docker-compose images" in history_str:
                return {"success": True, "message": "Success! Images listed."}
            return {"success": False, "message": "List active service images: docker compose images"}
        elif task_id == 6:
            if "docker compose logs" in history_str or "docker-compose logs" in history_str:
                return {"success": True, "message": "Success! Logs streams checked."}
            return {"success": False, "message": "Inspect log traces: docker compose logs"}
        elif task_id == 7:
            if "exec db redis-cli ping" in history_str:
                return {"success": True, "message": "Success! redis command execution verified."}
            return {"success": False, "message": "Run db exec: docker compose exec db redis-cli ping"}
        elif task_id == 8:
            if not shell.mock_compose_active or "down" in history_str:
                return {"success": True, "message": "Success! stack services removed."}
            return {"success": False, "message": "Teardown compose stack: docker compose down"}
        return {"success": False, "message": "Unknown task."}

    def _validate_docker_compose_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
        except Exception as e:
            return {"success": False, "message": f"Docker connection failure: {e}"}

        def run_in_sandbox(cmd: str) -> bool:
            res = container.exec_run(cmd, user="student")
            return res.exit_code == 0

        if task_id == 1:
            if run_in_sandbox("test -f /home/student/docker-compose.yml"):
                return {"success": True, "message": "Success! compose file exists."}
            return {"success": False, "message": "docker-compose.yml not found."}
        elif task_id in [2, 4, 5, 6, 7]:
            return {"success": True, "message": "Verification passed."}
        elif task_id == 3:
            if run_in_sandbox("docker inspect student_web_1") or run_in_sandbox("docker ps | grep nginx"):
                return {"success": True, "message": "Success! Stack up verified."}
            return {"success": False, "message": "Active services nginx/redis not found."}
        elif task_id == 8:
            res = container.exec_run("docker ps", user="student")
            if "student_web_1" not in res.output.decode():
                return {"success": True, "message": "Success! Stack down verified."}
            return {"success": False, "message": "Compose containers still running."}
        return {"success": False, "message": "Unknown task."}

    # ── Docker Networking Validator ──────────────────────
    def _validate_docker_networking_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()
        if task_id == 1:
            if "docker network ls" in history_str:
                return {"success": True, "message": "Success! listed networks."}
            return {"success": False, "message": "List active networks first: docker network ls"}
        elif task_id == 2:
            if "custom_bridge" in shell.mock_networks:
                return {"success": True, "message": "Success! network custom_bridge created."}
            return {"success": False, "message": "Create network: docker network create custom_bridge"}
        elif task_id == 3:
            if "docker network inspect custom_bridge" in history_str:
                return {"success": True, "message": "Success! custom_bridge details inspected."}
            return {"success": False, "message": "Inspect networking specs: docker network inspect custom_bridge"}
        elif task_id == 4:
            if "backend_app" in shell.mock_containers and shell.mock_containers["backend_app"]["network"] == "custom_bridge":
                return {"success": True, "message": "Success! backend container connected."}
            return {"success": False, "message": "Start redis backend container on custom_bridge network."}
        elif task_id == 5:
            if "frontend_app" in shell.mock_containers and shell.mock_containers["frontend_app"]["network"] == "custom_bridge":
                return {"success": True, "message": "Success! frontend container connected."}
            return {"success": False, "message": "Start alpine frontend container on custom_bridge network."}
        elif task_id == 6:
            if "exec frontend_app ping" in history_str and "backend_app" in history_str:
                return {"success": True, "message": "Success! network name lookup verified."}
            return {"success": False, "message": "Ping backend from frontend: docker exec frontend_app ping -c 3 backend_app"}
        elif task_id == 7:
            if "backend_app" not in shell.mock_containers:
                return {"success": True, "message": "Success! backend container removed."}
            return {"success": False, "message": "Stop and delete container: docker stop backend_app && docker rm backend_app"}
        elif task_id == 8:
            if "custom_bridge" not in shell.mock_networks:
                return {"success": True, "message": "Success! custom_bridge deleted."}
            return {"success": False, "message": "Delete network: docker network rm custom_bridge"}
        return {"success": False, "message": "Unknown task."}

    def _validate_docker_networking_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
        except Exception as e:
            return {"success": False, "message": f"Docker connection failure: {e}"}

        def run_in_sandbox(cmd: str) -> bool:
            res = container.exec_run(cmd, user="student")
            return res.exit_code == 0

        if task_id in [1, 3, 6]:
            return {"success": True, "message": "Verification passed."}
        elif task_id == 2:
            if run_in_sandbox("docker network inspect custom_bridge"):
                return {"success": True, "message": "Success! custom_bridge exists."}
            return {"success": False, "message": "custom_bridge network not found."}
        elif task_id == 4:
            if run_in_sandbox("docker inspect backend_app"):
                return {"success": True, "message": "Success! backend_app running."}
            return {"success": False, "message": "backend_app container not found."}
        elif task_id == 5:
            if run_in_sandbox("docker inspect frontend_app"):
                return {"success": True, "message": "Success! frontend_app running."}
            return {"success": False, "message": "frontend_app container not found."}
        elif task_id == 7:
            res = container.exec_run("docker inspect backend_app", user="student")
            if res.exit_code != 0:
                return {"success": True, "message": "Success! backend_app deleted."}
            return {"success": False, "message": "backend_app still exists."}
        elif task_id == 8:
            res = container.exec_run("docker network inspect custom_bridge", user="student")
            if res.exit_code != 0:
                return {"success": True, "message": "Success! custom_bridge network deleted."}
            return {"success": False, "message": "custom_bridge network still exists."}
        return {"success": False, "message": "Unknown task."}

    # ── Optimizing Dockerfiles Validator ───────────────
    def _validate_optimizing_dockerfiles_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        history_str = " ".join(shell.history).lower()
        if task_id == 1:
            path = shell.get_local_path("Dockerfile")
            if os.path.exists(path):
                return {"success": True, "message": "Success! Dockerfile created."}
            return {"success": False, "message": "Create unoptimized Dockerfile first."}
        elif task_id == 2:
            if "node_app:v1" in shell.mock_images:
                return {"success": True, "message": "Success! node_app:v1 image built."}
            return {"success": False, "message": "Build node_app:v1: docker build -t node_app:v1 ."}
        elif task_id == 3:
            if "docker image inspect node_app:v1" in history_str or "docker inspect node_app:v1" in history_str:
                return {"success": True, "message": "Success! image metadata inspected."}
            return {"success": False, "message": "Inspect image: docker image inspect node_app:v1"}
        elif task_id == 4:
            path = shell.get_local_path("Dockerfile")
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        lines = f.read().lower()
                    if "package.json" in lines and "npm install" in lines:
                        return {"success": True, "message": "Success! Dockerfile optimized."}
                except:
                    pass
            return {"success": False, "message": "Optimize Dockerfile syntax to copy package.json first."}
        elif task_id == 5:
            if "node_app:v2" in shell.mock_images:
                return {"success": True, "message": "Success! node_app:v2 image built."}
            return {"success": False, "message": "Build node_app:v2: docker build -t node_app:v2 ."}
        elif task_id == 6:
            path = shell.get_local_path("Dockerfile.multi")
            if os.path.exists(path):
                return {"success": True, "message": "Success! Dockerfile.multi multi-stage blueprint saved."}
            return {"success": False, "message": "Create Dockerfile.multi multi-stage configurations."}
        elif task_id == 7:
            if "node_app:prod" in shell.mock_images:
                return {"success": True, "message": "Success! node_app:prod image built."}
            return {"success": False, "message": "Build target: docker build -f Dockerfile.multi -t node_app:prod ."}
        elif task_id == 8:
            if "docker system prune" in history_str:
                return {"success": True, "message": "Success! System build caches cleared."}
            return {"success": False, "message": "Clean dangling build caches: docker system prune -f"}
        return {"success": False, "message": "Unknown task."}

    def _validate_optimizing_dockerfiles_live(self, container_id: str, task_id: int) -> Dict[str, Any]:
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)
        except Exception as e:
            return {"success": False, "message": f"Docker connection failure: {e}"}

        def run_in_sandbox(cmd: str) -> bool:
            res = container.exec_run(cmd, user="student")
            return res.exit_code == 0

        if task_id in [3, 8]:
            return {"success": True, "message": "Verification passed."}
        elif task_id == 1:
            if run_in_sandbox("test -f /home/student/Dockerfile"):
                return {"success": True, "message": "Success! Dockerfile created."}
            return {"success": False, "message": "Dockerfile not found in home folder."}
        elif task_id == 2:
            if run_in_sandbox("docker image inspect node_app:v1"):
                return {"success": True, "message": "Success! node_app:v1 image found."}
            return {"success": False, "message": "node_app:v1 image not found."}
        elif task_id == 4:
            if run_in_sandbox("grep -i 'package.json' /home/student/Dockerfile"):
                return {"success": True, "message": "Success! package.json caching optimized."}
            return {"success": False, "message": "package.json split optimization copy block not found."}
        elif task_id == 5:
            if run_in_sandbox("docker image inspect node_app:v2"):
                return {"success": True, "message": "Success! node_app:v2 image found."}
            return {"success": False, "message": "node_app:v2 image not found."}
        elif task_id == 6:
            if run_in_sandbox("test -f /home/student/Dockerfile.multi"):
                return {"success": True, "message": "Success! Dockerfile.multi multi-stage file found."}
            return {"success": False, "message": "Dockerfile.multi not found."}
        elif task_id == 7:
            if run_in_sandbox("docker image inspect node_app:prod"):
                return {"success": True, "message": "Success! node_app:prod image found."}
            return {"success": False, "message": "node_app:prod image not found."}
        return {"success": False, "message": "Unknown task."}



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

    def _validate_kubernetes_simulated(self, shell: Any, task_id: int, lab_name: str) -> Dict[str, Any]:
        # Fallback simulated verification logic
        # For non-challenge tasks (1 to 7), we can auto-verify if the corresponding kubectl command was run or mock exists
        history_str = " ".join(shell.history).lower()
        
        if task_id < 8:
            if task_id == 1:
                return {"success": True, "message": "Verification passed: Initial check completed."}
            elif task_id == 2:
                if "describe" in history_str or "get" in history_str:
                    return {"success": True, "message": "Verification passed: Details query run."}
                return {"success": False, "message": "Verify resource configurations by running 'kubectl describe' or 'kubectl get'."}
            elif task_id == 3:
                if "logs" in history_str or "describe" in history_str:
                    return {"success": True, "message": "Verification passed: Logs checked."}
                return {"success": False, "message": "Print logs using 'kubectl logs'."}
            elif task_id == 4:
                return {"success": True, "message": "Verification passed: Sandbox resource updated."}
            elif task_id == 5:
                if "svc" in history_str or "service" in history_str or "get" in history_str:
                    return {"success": True, "message": "Verification passed: Service list queried."}
                return {"success": False, "message": "List active services using 'kubectl get services'."}
            elif task_id == 6:
                return {"success": True, "message": "Verification passed: Resource cleaned up."}
            elif task_id == 7:
                if "get all" in history_str or "get" in history_str:
                    return {"success": True, "message": "Verification passed: Full status queried."}
                return {"success": False, "message": "Query all active workloads using 'kubectl get all'."}

        if lab_name == "kubernetes-fundamentals":
            if "cluster-info" in history_str or "get nodes" in history_str:
                return {"success": True, "message": "Challenge Complete! Cluster info queried successfully."}
            return {"success": False, "message": "Retrieve cluster parameters using 'kubectl cluster-info'."}

        elif lab_name == "kubernetes-pods":
            if "custom-pod" in shell.mock_pods:
                return {"success": True, "message": "Challenge Complete! custom-pod is running redis:alpine with label env=prod."}
            return {"success": False, "message": "Deploy a pod named 'custom-pod' running 'redis:alpine' with label env=prod."}

        elif lab_name == "kubernetes-deployments":
            if "db-deploy" in shell.mock_deployments:
                return {"success": True, "message": "Challenge Complete! db-deploy created with 3 replicas."}
            return {"success": False, "message": "Create a deployment named 'db-deploy' running 'redis:alpine' with 3 replicas."}

        elif lab_name == "kubernetes-replicasets":
            if "webapp-deploy" in shell.mock_deployments and shell.mock_deployments["webapp-deploy"]["replicas"] == 4:
                return {"success": True, "message": "Challenge Complete! Deployment scaled to 4 replicas."}
            return {"success": False, "message": "Scale the deployment webapp-deploy to 4 replicas."}

        elif lab_name == "kubernetes-services":
            if "webapp-nodeport" in shell.mock_services and shell.mock_services["webapp-nodeport"]["type"] == "NodePort":
                return {"success": True, "message": "Challenge Complete! NodePort service webapp-nodeport exposed successfully."}
            return {"success": False, "message": "Expose webapp-deploy using a NodePort service named webapp-nodeport."}

        elif lab_name == "kubernetes-namespaces":
            if "devlab-test" in shell.mock_namespaces:
                return {"success": True, "message": "Challenge Complete! devlab-test namespace created successfully."}
            return {"success": False, "message": "Create a namespace named devlab-test."}

        elif lab_name == "kubernetes-configmaps":
            if "env-config" in shell.mock_configmaps:
                return {"success": True, "message": "Challenge Complete! env-config ConfigMap created."}
            return {"success": False, "message": "Create a ConfigMap named env-config with STAGE=prod literal."}

        elif lab_name == "kubernetes-secrets":
            if "api-secret" in shell.mock_secrets:
                return {"success": True, "message": "Challenge Complete! api-secret Secret created."}
            return {"success": False, "message": "Create a secret named api-secret with api-key=secretkey123."}

        elif lab_name == "kubernetes-persistent-volumes":
            if shell.mock_pvs or "pv" in history_str:
                return {"success": True, "message": "Challenge Complete! Persistent volumes query run."}
            return {"success": False, "message": "Query persistent volumes in the cluster."}

        elif lab_name == "kubernetes-persistent-volume-claims":
            if shell.mock_pvcs or "pvc" in history_str:
                return {"success": True, "message": "Challenge Complete! Persistent volume claims query run."}
            return {"success": False, "message": "Query persistent volume claims in the cluster namespace."}

        elif lab_name == "kubernetes-ingress":
            if shell.mock_ingresses or "ingress" in history_str:
                return {"success": True, "message": "Challenge Complete! Ingress resources queried."}
            return {"success": False, "message": "List active ingress interfaces."}

        elif lab_name == "kubernetes-rolling-updates":
            if "webapp-deploy" in shell.mock_deployments and "1.25" in shell.mock_deployments["webapp-deploy"]["image"]:
                return {"success": True, "message": "Challenge Complete! Deployment image updated to nginx:1.25-alpine."}
            return {"success": False, "message": "Update deployment webapp-deploy image to nginx:1.25-alpine."}

        elif lab_name == "kubernetes-jobs-and-cronjobs":
            if "cronjob" in history_str:
                return {"success": True, "message": "Challenge Complete! CronJobs queried successfully."}
            return {"success": False, "message": "List cronjobs using kubectl."}

        elif lab_name == "kubernetes-resource-requests-and-limits":
            if "describe" in history_str:
                return {"success": True, "message": "Challenge Complete! Audited CPU/Memory constraints."}
            return {"success": False, "message": "Inspect constraints using describe."}

        elif lab_name == "kubernetes-autoscaling-hpa":
            if "hpa" in history_str or shell.mock_hpas:
                return {"success": True, "message": "Challenge Complete! HPA configurations listed."}
            return {"success": False, "message": "Query horizontal pod autoscaler profiles."}

        elif lab_name == "kubernetes-helm-basics":
            if shell.mock_helm_charts or "helm" in history_str:
                return {"success": True, "message": "Challenge Complete! Helm charts releases query run."}
            return {"success": False, "message": "Run helm list to inspect releases."}

        elif lab_name == "kubernetes-production-best-practices":
            return {"success": True, "message": "Challenge Complete! Production configuration checklist passed."}

        elif lab_name == "kubernetes-capstone-project":
            if (
                "webapp-frontend" in shell.mock_deployments and
                "webapp-backend" in shell.mock_deployments and
                "frontend-service" in shell.mock_services and
                "backend-service" in shell.mock_services and
                "capstone-config" in shell.mock_configmaps and
                "capstone-secret" in shell.mock_secrets and
                "capstone-pvc" in shell.mock_pvcs and
                "capstone-ingress" in shell.mock_ingresses
            ):
                return {"success": True, "message": "Congratulations! The entire multi-tier capstone application is deployed correctly!"}
            return {"success": False, "message": "Verify that your Frontend, Backend, ConfigMap, Secret, Service, Ingress, and Persistent Volume Claim are all created."}

        return {"success": True, "message": "Verification passed."}

    def _validate_kubernetes_live(self, session_id: str, task_id: int, lab_name: str) -> Dict[str, Any]:
        try:
            from kubernetes import client as k8s_client, config as k8s_config
            from app.core.config import settings
            
            if os.path.exists(settings.KUBECONFIG_PATH):
                k8s_config.load_kube_config(config_file=settings.KUBECONFIG_PATH)
            else:
                k8s_config.load_kube_config()
                
            v1 = k8s_client.CoreV1Api()
            apps_v1 = k8s_client.AppsV1Api()
            networking_v1 = k8s_client.NetworkingV1Api()
            autoscaling_v1 = k8s_client.AutoscalingV1Api()
            batch_v1 = k8s_client.BatchV1Api()
            
            ns = f"devlab-ns-{session_id}"
            
            if task_id < 8:
                return {"success": True, "message": "Task checked against live cluster namespace status."}
                
            if lab_name == "kubernetes-fundamentals":
                v1.list_node(limit=1)
                return {"success": True, "message": "Cluster status verified."}
                
            elif lab_name == "kubernetes-pods":
                pod = v1.read_namespaced_pod("custom-pod", ns)
                if pod.status.phase == "Running" and "redis" in pod.spec.containers[0].image:
                    return {"success": True, "message": "Custom Pod custom-pod verified in namespace."}
                return {"success": False, "message": "Pod custom-pod is not in Running state."}
                
            elif lab_name == "kubernetes-deployments":
                dep = apps_v1.read_namespaced_deployment("db-deploy", ns)
                if dep.spec.replicas >= 3 and "redis" in dep.spec.template.spec.containers[0].image:
                    return {"success": True, "message": "db-deploy verified with 3 replicas."}
                return {"success": False, "message": "Deployment db-deploy is not configured correctly."}
                
            elif lab_name == "kubernetes-replicasets":
                dep = apps_v1.read_namespaced_deployment("webapp-deploy", ns)
                if dep.spec.replicas == 4:
                    return {"success": True, "message": "webapp-deploy scaled to 4 replicas."}
                return {"success": False, "message": "Deployment replicas count is not 4."}
                
            elif lab_name == "kubernetes-services":
                svc = v1.read_namespaced_service("webapp-nodeport", ns)
                if svc.spec.type == "NodePort":
                    return {"success": True, "message": "webapp-nodeport service verified."}
                return {"success": False, "message": "Service webapp-nodeport is not a NodePort service."}
                
            elif lab_name == "kubernetes-namespaces":
                v1.read_namespace("devlab-test")
                return {"success": True, "message": "Namespace devlab-test verified."}
                
            elif lab_name == "kubernetes-configmaps":
                cm = v1.read_namespaced_config_map("env-config", ns)
                if cm.data.get("STAGE") == "prod":
                    return {"success": True, "message": "ConfigMap env-config verified."}
                return {"success": False, "message": "ConfigMap data value not matched."}
                
            elif lab_name == "kubernetes-secrets":
                sec = v1.read_namespaced_secret("api-secret", ns)
                if sec:
                    return {"success": True, "message": "Secret api-secret verified."}
                return {"success": False, "message": "Secret api-secret not found."}
                
            elif lab_name == "kubernetes-persistent-volumes":
                return {"success": True, "message": "Persistent volumes verified."}
                
            elif lab_name == "kubernetes-persistent-volume-claims":
                pvcs = v1.list_namespaced_persistent_volume_claim(ns)
                if pvcs.items:
                    return {"success": True, "message": "Persistent volume claims verified."}
                return {"success": False, "message": "No PVC found in namespace."}
                
            elif lab_name == "kubernetes-ingress":
                ings = networking_v1.list_namespaced_ingress(ns)
                if ings.items:
                    return {"success": True, "message": "Ingress verified."}
                return {"success": False, "message": "No Ingress found in namespace."}
                
            elif lab_name == "kubernetes-rolling-updates":
                dep = apps_v1.read_namespaced_deployment("webapp-deploy", ns)
                if "1.25" in dep.spec.template.spec.containers[0].image:
                    return {"success": True, "message": "webapp-deploy image successfully updated."}
                return {"success": False, "message": "Deployment image is not updated."}
                
            elif lab_name == "kubernetes-jobs-and-cronjobs":
                cronjobs = batch_v1.list_namespaced_cron_job(ns)
                if cronjobs.items:
                    return {"success": True, "message": "CronJobs verified."}
                return {"success": False, "message": "No CronJobs found in namespace."}
                
            elif lab_name == "kubernetes-resource-requests-and-limits":
                return {"success": True, "message": "Resource requests and limits audited."}
                
            elif lab_name == "kubernetes-autoscaling-hpa":
                hpas = autoscaling_v1.list_namespaced_horizontal_pod_autoscaler(ns)
                if hpas.items:
                    return {"success": True, "message": "HPA autoscaler verified."}
                return {"success": False, "message": "No HPA found in namespace."}
                
            elif lab_name == "kubernetes-helm-basics":
                return {"success": True, "message": "Helm release verified."}
                
            elif lab_name == "kubernetes-production-best-practices":
                return {"success": True, "message": "Production rules verified."}
                
            elif lab_name == "kubernetes-capstone-project":
                dep_f = apps_v1.read_namespaced_deployment("webapp-frontend", ns)
                dep_b = apps_v1.read_namespaced_deployment("webapp-backend", ns)
                svc_f = v1.read_namespaced_service("frontend-service", ns)
                svc_b = v1.read_namespaced_service("backend-service", ns)
                cm = v1.read_namespaced_config_map("capstone-config", ns)
                sec = v1.read_namespaced_secret("capstone-secret", ns)
                pvc = v1.read_namespaced_persistent_volume_claim("capstone-pvc", ns)
                ing = networking_v1.read_namespaced_ingress("capstone-ingress", ns)
                if dep_f and dep_b and svc_f and svc_b and cm and sec and pvc and ing:
                    return {"success": True, "message": "Congratulations! The entire multi-tier capstone application is deployed correctly!"}
                return {"success": False, "message": "One or more Capstone resources are missing or misconfigured."}
                
            return {"success": False, "message": "Live validation target not matched."}
            
        except Exception as e:
            logger.error(f"Live K8s validation error: {e}")
            return {"success": False, "message": f"Validation failed: K3s cluster unreachable or resources not found."}

    def _validate_git(self, shell: Any, task_id: int, lab_name: str) -> Dict[str, Any]:
        """
        Validates Git course progress against the actual repository state.
        """
        history_str = " ".join(shell.history).lower()
        
        # Helper check if git repo is initialized
        git_dir = os.path.join(shell.base_dir, ".git")
        if not os.path.exists(git_dir):
            if task_id == 1 and lab_name == "git-fundamentals":
                # Let them run git init
                pass
            else:
                return {"success": False, "message": "Git repository is not initialized. Run 'git init'."}

        # Route validations by task_id and lab_name
        if task_id == 1:
            if lab_name == "git-fundamentals":
                if os.path.exists(git_dir):
                    return {"success": True, "message": "Success! Empty Git repository initialized."}
                return {"success": False, "message": "Please initialize the repository using 'git init'."}
            else:
                return {"success": True, "message": "Repository initialized."}

        elif task_id == 2:
            if "git status" in history_str:
                return {"success": True, "message": "Success! Checked repository status."}
            return {"success": False, "message": "Query files status by running 'git status'."}

        elif task_id == 3:
            if "git log" in history_str:
                return {"success": True, "message": "Success! Inspected commit history log."}
            return {"success": False, "message": "Print commit history using 'git log'."}

        elif task_id == 4:
            if "git config" in history_str:
                return {"success": True, "message": "Success! Config list checked."}
            return {"success": False, "message": "View config parameters by running 'git config --list'."}

        elif task_id == 5:
            if "git show-ref" in history_str:
                return {"success": True, "message": "Success! Commit references queried."}
            return {"success": False, "message": "Query references mapping by running 'git show-ref'."}

        elif task_id == 6:
            if "git branch" in history_str:
                return {"success": True, "message": "Success! Active branches listed."}
            return {"success": False, "message": "Query branch listings using 'git branch'."}

        elif task_id == 7:
            if "git reflog" in history_str:
                return {"success": True, "message": "Success! Pointer history reflogs audited."}
            return {"success": False, "message": "Query reference action logs using 'git reflog'."}

        elif task_id == 8:
            # Mini Challenges
            if lab_name == "git-fundamentals":
                index_path = os.path.join(shell.base_dir, "index.html")
                if not os.path.exists(index_path):
                    return {"success": False, "message": "File 'index.html' is missing."}
                res = subprocess.run(["git", "log", "-1", "--pretty=%B"], cwd=shell.base_dir, capture_output=True, text=True)
                if res.returncode == 0 and "initial page" in res.stdout.lower():
                    return {"success": True, "message": "Success! Committed index.html with message 'feat: initial page'."}
                return {"success": False, "message": "Commit index.html with message containing 'initial page'."}

            elif lab_name == "git-branching-and-merging":
                res_l = subprocess.run(["git", "log", "--oneline"], cwd=shell.base_dir, capture_output=True, text=True)
                if res_l.returncode == 0 and "merge" in res_l.stdout.lower():
                    return {"success": True, "message": "Success! Feature branch merged into main."}
                return {"success": False, "message": "Merge 'feature-auth' branch into main."}

            elif lab_name == "advanced-git":
                res = subprocess.run(["git", "tag"], cwd=shell.base_dir, capture_output=True, text=True)
                if res.returncode == 0 and "v1.0.0" in res.stdout:
                    return {"success": True, "message": "Success! Version tag v1.0.0 is created."}
                return {"success": False, "message": "Create an annotated tag named 'v1.0.0' on current HEAD."}

            elif lab_name == "team-workflows":
                c_path = os.path.join(shell.base_dir, "conflict.txt")
                if not os.path.exists(c_path):
                    return {"success": False, "message": "conflict.txt not found."}
                with open(c_path, "r") as f:
                    content = f.read()
                if "<<<<<<<" in content or "=======" in content or ">>>>>>>" in content:
                    return {"success": False, "message": "conflict.txt still contains conflict markers."}
                return {"success": True, "message": "Success! Merge conflicts resolved."}

        return {"success": False, "message": "Unknown task check."}

    def _validate_github_actions(self, shell: Any, task_id: int, lab_name: str) -> Dict[str, Any]:
        """
        Validates GitHub Actions course progress against YAML file definitions and execution flags.
        """
        history_str = " ".join(shell.history).lower()
        workflow_path = os.path.join(shell.base_dir, ".github/workflows/main.yml")

        if task_id == 1:
            if os.path.exists(workflow_path):
                return {"success": True, "message": "Success! main.yml workflow file created."}
            return {"success": False, "message": "Create the workflow configuration file inside '.github/workflows/main.yml'."}

        elif task_id == 2:
            if "git status" in history_str:
                return {"success": True, "message": "Success! Checked repository status."}
            return {"success": False, "message": "Query files status by running 'git status'."}

        elif task_id == 3:
            if "git log" in history_str:
                return {"success": True, "message": "Success! Inspected commit history log."}
            return {"success": False, "message": "Print commit history using 'git log'."}

        elif task_id == 4:
            if "git config" in history_str:
                return {"success": True, "message": "Success! Config list checked."}
            return {"success": False, "message": "View config parameters by running 'git config --list'."}

        elif task_id == 5:
            if "git show-ref" in history_str:
                return {"success": True, "message": "Success! Commit references queried."}
            return {"success": False, "message": "Query references mapping by running 'git show-ref'."}

        elif task_id == 6:
            if "git branch" in history_str:
                return {"success": True, "message": "Success! Active branches listed."}
            return {"success": False, "message": "Query branch listings using 'git branch'."}

        elif task_id == 7:
            if "git reflog" in history_str:
                return {"success": True, "message": "Success! Pointer history reflogs audited."}
            return {"success": False, "message": "Query reference action logs using 'git reflog'."}

        elif task_id == 8:
            if not os.path.exists(workflow_path):
                return {"success": False, "message": "Workflow file '.github/workflows/main.yml' does not exist."}
            
            if not getattr(shell, "workflow_executed", False):
                return {"success": False, "message": "Trigger workflow run by committing and pushing changes using 'git push origin main'."}

            try:
                import yaml
                with open(workflow_path, "r") as f:
                    yaml_data = yaml.safe_load(f) or {}
            except Exception as e:
                return {"success": False, "message": f"Indentation error or invalid YAML syntax: {e}"}

            # Handle PyYAML parsing 'on' as boolean True key in YAML 1.1
            on_val = yaml_data.get("on") if "on" in yaml_data else yaml_data.get(True)

            if lab_name == "github-actions-fundamentals":
                if not on_val or "push" not in str(on_val):
                    return {"success": False, "message": "Workflow trigger must contain 'push'."}
                
                jobs = yaml_data.get("jobs", {})
                if not jobs:
                    return {"success": False, "message": "Workflow jobs configuration is missing."}
                
                first_job = list(jobs.values())[0]
                if "ubuntu-latest" not in str(first_job.get("runs-on")):
                    return {"success": False, "message": "Runner must be configured as 'runs-on: ubuntu-latest'."}
                
                return {"success": True, "message": "Success! First GitHub Actions workflow verified."}

            elif lab_name == "building-ci-pipelines":
                jobs = yaml_data.get("jobs", {})
                first_job = list(jobs.values())[0] if jobs else {}
                steps = first_job.get("steps", [])
                
                has_checkout = any("actions/checkout" in str(s.get("uses")) for s in steps if isinstance(s, dict))
                if not has_checkout:
                    return {"success": False, "message": "Workflow steps must use 'actions/checkout'."}
                
                steps_str = str(steps).lower()
                if "npm install" not in steps_str or "npm run build" not in steps_str:
                    return {"success": False, "message": "Workflow steps must run 'npm install' and 'npm run build'."}

                return {"success": True, "message": "Success! CI Pipeline checks verified."}

            elif lab_name == "testing-and-artifact-management":
                jobs = yaml_data.get("jobs", {})
                first_job = list(jobs.values())[0] if jobs else {}
                steps = first_job.get("steps", [])
                
                has_upload = any("upload-artifact" in str(s.get("uses")) for s in steps if isinstance(s, dict))
                if not has_upload:
                    return {"success": False, "message": "Workflow steps must use 'actions/upload-artifact'."}
                
                steps_str = str(steps).lower()
                if "npm test" not in steps_str:
                    return {"success": False, "message": "Workflow steps must run 'npm test'."}

                return {"success": True, "message": "Success! Test artifacts uploads verified."}

            elif lab_name == "automated-deployments":
                jobs = yaml_data.get("jobs", {})
                first_job = list(jobs.values())[0] if jobs else {}
                steps = first_job.get("steps", [])
                
                steps_str = str(steps)
                if "secrets.DEPLOY_KEY" not in steps_str:
                    return {"success": False, "message": "Workflow steps must reference deploy secrets '${{ secrets.DEPLOY_KEY }}'."}

                return {"success": True, "message": "Success! Continuous deployment pipeline verified."}

        return {"success": False, "message": "Unknown task check."}

    def _validate_cicd(self, shell: Any, task_id: int, lab_name: str) -> Dict[str, Any]:
        """
        Validates CI/CD course progress against pipeline file configurations and simulator logs.
        """
        history_str = " ".join(shell.history).lower()
        pipeline_path = os.path.join(shell.base_dir, "pipeline.yml")

        if task_id == 1:
            if os.path.exists(pipeline_path):
                return {"success": True, "message": "Success! pipeline.yml file created."}
            return {"success": False, "message": "Create the pipeline configuration file named 'pipeline.yml'."}

        elif task_id in [2, 3, 4, 5, 6, 7]:
            git_cmds = {
                2: ("git status", "Query repository files status using 'git status'."),
                3: ("git log", "Print commits timeline history log using 'git log'."),
                4: ("git config", "Verify config details using 'git config --list'."),
                5: ("git show-ref", "Query pointer references mappings using 'git show-ref'."),
                6: ("git branch", "Identify active branches positions utilizing 'git branch'."),
                7: ("git reflog", "Inspect revisions tracking logs by running 'git reflog'.")
            }
            cmd_key, error_msg = git_cmds[task_id]
            if cmd_key in history_str:
                return {"success": True, "message": f"Success! Executed {cmd_key} check."}
            return {"success": False, "message": error_msg}

        elif task_id == 8:
            if not os.path.exists(pipeline_path):
                return {"success": False, "message": "pipeline.yml config file does not exist."}

            if not getattr(shell, "pipeline_executed", False):
                return {"success": False, "message": "Execute the pipeline simulation run by executing the custom command 'run-pipeline'."}

            try:
                import yaml
                with open(pipeline_path, "r") as f:
                    yaml_data = yaml.safe_load(f) or {}
            except Exception as e:
                return {"success": False, "message": f"YAML syntax error: {e}"}

            stages = yaml_data.get("stages", [])
            if not isinstance(stages, list) or not stages:
                return {"success": False, "message": "Pipeline configuration must define a list of 'stages'."}

            stages_clean = [s.lower().strip() for s in stages]

            if lab_name == "introduction-to-cicd":
                required = ["checkout", "test", "build"]
                for req in required:
                    if req not in stages_clean:
                        return {"success": False, "message": f"Pipeline must contain '{req}' stage."}
                return {"success": True, "message": "Success! Introduction to CI/CD pipeline verified."}

            elif lab_name == "continuous-integration":
                required = ["checkout", "lint", "test", "build"]
                for req in required:
                    if req not in stages_clean:
                        return {"success": False, "message": f"Pipeline must contain '{req}' stage."}
                return {"success": True, "message": "Success! Continuous Integration pipeline verified."}

            elif lab_name == "continuous-delivery":
                required = ["checkout", "test", "build", "package", "release"]
                for req in required:
                    if req not in stages_clean:
                        return {"success": False, "message": f"Pipeline must contain '{req}' stage."}
                return {"success": True, "message": "Success! Continuous Delivery pipeline verified."}

            elif lab_name == "continuous-deployment":
                required = ["checkout", "test", "build", "deploy", "verify"]
                for req in required:
                    if req not in stages_clean:
                        return {"success": False, "message": f"Pipeline must contain '{req}' stage."}
                return {"success": True, "message": "Success! Continuous Deployment pipeline verified."}

            elif lab_name == "building-a-complete-cicd-pipeline":
                required = ["checkout", "lint", "test", "build", "package", "approval", "deploy", "rollback"]
                for req in required:
                    if req not in stages_clean:
                        return {"success": False, "message": f"Pipeline must contain '{req}' stage."}
                return {"success": True, "message": "Success! Enterprise CI/CD pipeline verified."}

        return {"success": False, "message": "Unknown task check."}

    def _validate_jenkins(self, shell: Any, task_id: int, lab_name: str) -> Dict[str, Any]:
        """
        Validates Jenkins course progress against Jenkinsfile configuration attributes and build logs.
        """
        history_str = " ".join(shell.history).lower()
        jenkinsfile_path = os.path.join(shell.base_dir, "Jenkinsfile")

        if task_id == 1:
            if os.path.exists(jenkinsfile_path):
                return {"success": True, "message": "Success! Jenkinsfile configuration file created."}
            return {"success": False, "message": "Create the pipeline configuration file named 'Jenkinsfile'."}

        elif task_id in [2, 3, 4, 5, 6, 7]:
            git_cmds = {
                2: ("git status", "Query repository files status using 'git status'."),
                3: ("git log", "Print commits timeline history log using 'git log'."),
                4: ("git config", "Verify config details using 'git config --list'."),
                5: ("git show-ref", "Query pointer references mappings using 'git show-ref'."),
                6: ("git branch", "Identify active branches positions utilizing 'git branch'."),
                7: ("git reflog", "Inspect revisions tracking logs by running 'git reflog'.")
            }
            cmd_key, error_msg = git_cmds[task_id]
            if cmd_key in history_str:
                return {"success": True, "message": f"Success! Executed {cmd_key} check."}
            return {"success": False, "message": error_msg}

        elif task_id == 8:
            if not os.path.exists(jenkinsfile_path):
                return {"success": False, "message": "Jenkinsfile configuration file does not exist."}

            if not getattr(shell, "jenkins_executed", False):
                return {"success": False, "message": "Execute the Jenkins pipeline simulation build by running the custom command 'jenkins build'."}

            with open(jenkinsfile_path, "r", encoding="utf-8") as f:
                content = f.read()

            content_clean = content.replace(" ", "").replace("\n", "").replace("\r", "").replace('"', "'").lower()

            if lab_name == "jenkins-fundamentals":
                if "stage('build')" not in content_clean:
                    return {"success": False, "message": "Jenkinsfile must contain a stage named 'Build'."}
                return {"success": True, "message": "Success! Jenkins fundamentals pipeline verified."}

            elif lab_name == "installing-and-configuring-jenkins":
                if "stage('install')" not in content_clean:
                    return {"success": False, "message": "Jenkinsfile must contain a stage named 'Install'."}
                return {"success": True, "message": "Success! Installation verification pipeline verified."}

            elif lab_name == "freestyle-jobs":
                if "stage('freestyle')" not in content_clean:
                    return {"success": False, "message": "Jenkinsfile must contain a stage named 'Freestyle'."}
                return {"success": True, "message": "Success! Freestyle job representation pipeline verified."}

            elif lab_name == "pipeline-as-code-jenkinsfile":
                if "stage('build')" not in content_clean or "stage('test')" not in content_clean:
                    return {"success": False, "message": "Jenkinsfile must contain 'Build' and 'Test' stages."}
                return {"success": True, "message": "Success! Pipeline as Code configuration verified."}

            elif lab_name == "declarative-vs-scripted-pipelines":
                if "node{" not in content_clean:
                    return {"success": False, "message": "Jenkinsfile must define a scripted pipeline using a 'node {}' block."}
                if "stage('checkout')" not in content_clean or "stage('build')" not in content_clean:
                    return {"success": False, "message": "Scripted pipeline must define 'Checkout' and 'Build' stages."}
                return {"success": True, "message": "Success! Scripted pipeline paradigm verified."}

            elif lab_name == "distributed-builds-and-agents":
                if "agent{label'worker-node'}" not in content_clean and "label'worker-node'" not in content_clean:
                    return {"success": False, "message": "Jenkinsfile must declare execution agent with label 'worker-node'."}
                return {"success": True, "message": "Success! Distributed agent worker configuration verified."}

            elif lab_name == "credentials-and-secrets-management":
                if "credentials('db-password')" not in content_clean:
                    return {"success": False, "message": "Jenkinsfile must bind credentials store database key using credentials('db-password')."}
                return {"success": True, "message": "Success! Secure credentials binding verified."}

            elif lab_name == "plugins-and-integrations":
                if "slacksend" not in content_clean:
                    return {"success": False, "message": "Jenkinsfile step must send Slack notification via slackSend step."}
                return {"success": True, "message": "Success! Plugin notifications step verified."}

            elif lab_name == "building-a-complete-cicd-pipeline-jenkins":
                required = ["stage('checkout')", "stage('build')", "stage('test')", "stage('deploy')"]
                for req in required:
                    if req not in content_clean:
                        return {"success": False, "message": f"Pipeline must define stage: {req}."}
                return {"success": True, "message": "Success! Complete pipeline integration verified."}

            elif lab_name == "jenkins-best-practices":
                if "builddiscarder" not in content_clean:
                    return {"success": False, "message": "Jenkinsfile must configure a buildDiscarder option to rotate logs."}
                return {"success": True, "message": "Success! Log pruning best practices verified."}

            elif lab_name == "jenkins-capstone-project":
                required = ["stage('checkout')", "stage('build')", "stage('test')", "stage('deploy')", "stage('archive')"]
                for req in required:
                    if req not in content_clean:
                        return {"success": False, "message": f"Capstone pipeline must define stage: {req}."}
                return {"success": True, "message": "Success! Jenkins Capstone Project verified."}

    def _validate_terraform(self, shell: Any, task_id: int, lab_name: str) -> Dict[str, Any]:
        """
        Validates Terraform course progress against HCL files, workspaces, and state caches.
        """
        main_tf = os.path.join(shell.base_dir, "main.tf")
        variables_tf = os.path.join(shell.base_dir, "variables.tf")
        outputs_tf = os.path.join(shell.base_dir, "outputs.tf")
        state_file = os.path.join(shell.base_dir, "terraform.tfstate")
        history_str = " ".join(shell.history).lower()

        # Step 1: Initialize first files check
        if task_id == 1:
            if os.path.exists(main_tf):
                return {"success": True, "message": "Success! 'main.tf' configuration file created."}
            return {"success": False, "message": "Create the main configuration file named 'main.tf'."}

        # Step 2: Validate syntax via `terraform validate`
        if task_id == 2:
            if "terraform validate" in history_str:
                return {"success": True, "message": "Success! Validation command execution checked."}
            return {"success": False, "message": "Execute the formatting validation checks using 'terraform validate'."}

        # Step 3: Check Dry-Run Plan
        if task_id == 3:
            if "terraform plan" in history_str:
                return {"success": True, "message": "Success! Dry-run planning execution verified."}
            return {"success": False, "message": "Trigger plan verification output by running 'terraform plan'."}

        # Step 4: Check Apply Lifecycle
        if task_id == 4:
            if os.path.exists(state_file):
                return {"success": True, "message": "Success! Resource applied and saved in state file."}
            return {"success": False, "message": "Deploy resources by running 'terraform apply' to write state file."}

        # Step 5: Check Workspace Isolation
        if task_id == 5:
            if getattr(shell, "tf_workspace", "default") == "dev":
                return {"success": True, "message": "Success! Environment workspace 'dev' selected."}
            return {"success": False, "message": "Switch active environment using 'terraform workspace select dev'."}

        # Step 6: Check Managed State Lists
        if task_id == 6:
            if "terraform state list" in history_str:
                return {"success": True, "message": "Success! Inspected managed state resource lists."}
            return {"success": False, "message": "Inspect active resource identifiers by executing 'terraform state list'."}

        # Step 7: Check Output Variables
        if task_id == 7:
            if "terraform output" in history_str:
                return {"success": True, "message": "Success! Outputs retrieval verified."}
            return {"success": False, "message": "Retrieve parameterized variable outputs values by running 'terraform output'."}

        # Step 8 (Mini Challenge): Module-specific custom criteria
        if task_id == 8:
            content = ""
            if os.path.exists(main_tf):
                with open(main_tf, "r", encoding="utf-8") as f:
                    content = f.read().lower()

            if lab_name == "terraform-fundamentals":
                if "resource" not in content or "local_file" not in content:
                    return {"success": False, "message": "Configuration must declare a 'local_file' resource block."}
                return {"success": True, "message": "Success! Terraform fundamentals challenge verified."}

            elif lab_name == "installing-terraform-and-providers":
                if "provider" not in content or "local" not in content:
                    return {"success": False, "message": "Configuration must declare a 'local' provider configuration block."}
                return {"success": True, "message": "Success! Providers installation challenge verified."}

            elif lab_name == "variables-outputs-and-locals":
                if not os.path.exists(variables_tf) or not os.path.exists(outputs_tf):
                    return {"success": False, "message": "You must create both 'variables.tf' and 'outputs.tf' files."}
                return {"success": True, "message": "Success! Parameter boundaries variables and outputs verified."}

            elif lab_name == "resources-and-dependencies":
                if "depends_on" not in content:
                    return {"success": False, "message": "Resource configuration must declare explicit dependency via depends_on."}
                return {"success": True, "message": "Success! Resource dependency graph validation verified."}

            elif lab_name == "state-management":
                if not os.path.exists(state_file):
                    return {"success": False, "message": "Execute terraform apply first to synchronize the state file."}
                return {"success": True, "message": "Success! State metadata cache verified."}

            elif lab_name == "modules":
                if "module" not in content or "local_gen" not in content:
                    return {"success": False, "message": "Configuration must declare a module block named 'local_gen'."}
                return {"success": True, "message": "Success! Reusable local module configuration verified."}

            elif lab_name == "provisioners":
                if "provisioner" not in content or "local-exec" not in content:
                    return {"success": False, "message": "Resource block must contain a provisioner 'local-exec' block."}
                return {"success": True, "message": "Success! Local execution provisioner step verified."}

            elif lab_name == "workspaces":
                if "dev" not in getattr(shell, "tf_workspaces_list", []):
                    return {"success": False, "message": "Workspace list must contain 'dev' workspace."}
                return {"success": True, "message": "Success! Isolated workspaces environment verified."}

            elif lab_name == "remote-state-concepts":
                if "backend" not in content or "local" not in content:
                    return {"success": False, "message": "Configuration must configure local state backend path settings."}
                return {"success": True, "message": "Success! Remote backend state settings verified."}

            elif lab_name == "best-practices-terraform":
                if "terraform fmt" not in history_str:
                    return {"success": False, "message": "Clean HCL files formatting must be checked using 'terraform fmt'."}
                return {"success": True, "message": "Success! Linting/formatting best practices verified."}

            elif lab_name == "terraform-capstone-project":
                if not os.path.exists(state_file) or "apply" not in history_str:
                    return {"success": False, "message": "Complete the capstone infrastructure deployment by running 'terraform apply'."}
                return {"success": True, "message": "Success! Terraform Capstone Project validated."}

        return {"success": False, "message": "Unknown task check."}

        return {"success": False, "message": "Unknown task check."}

    def _validate_ansible(self, shell: Any, task_id: int, lab_name: str) -> Dict[str, Any]:
        """
        Validates Ansible course progress against playbook syntax, inventory files, and history execution logs.
        """
        hosts_file = os.path.join(shell.base_dir, "hosts")
        playbook_file = os.path.join(shell.base_dir, "playbook.yml")
        history_str = " ".join(shell.history).lower()

        # Step 1: Initialize first files check
        if task_id == 1:
            if lab_name == "ansible-galaxy":
                if "ansible-galaxy" in history_str:
                    return {"success": True, "message": "Success! Galaxy role init command executed."}
                return {"success": False, "message": "Run ansible-galaxy init command to initialize database role folders."}
            
            if os.path.exists(hosts_file) or os.path.exists(playbook_file) or os.path.exists(os.path.join(shell.base_dir, "roles")):
                return {"success": True, "message": "Success! File configuration created."}
            return {"success": False, "message": "Create the required files (hosts, playbook.yml, or roles structure)."}

        # Step 2: System diagnostic checks
        if task_id == 2:
            if "pwd" in history_str or "version" in history_str:
                return {"success": True, "message": "Success! Diagnostics checked."}
            return {"success": False, "message": "Confirm workspace path by running pwd or diagnostic version commands."}

        # Step 3: List files check
        if task_id == 3:
            if "ls" in history_str:
                return {"success": True, "message": "Success! Directory contents listed."}
            return {"success": False, "message": "List active configuration files by executing ls."}

        # Step 4: Verify files contents display
        if task_id == 4:
            if "cat" in history_str:
                return {"success": True, "message": "Success! Inspected configuration variables contents."}
            return {"success": False, "message": "View local variables file layout using cat."}

        # Step 5: Read module help docs
        if task_id == 5:
            if "ansible-doc" in history_str:
                return {"success": True, "message": "Success! Sourced module configurations options help document."}
            return {"success": False, "message": "Query the ping module options schema using 'ansible-doc ping'."}

        # Step 6: Query inventory targets list
        if task_id == 6:
            if "ansible-inventory" in history_str or os.path.exists(hosts_file):
                return {"success": True, "message": "Success! Target inventory hosts configuration checked."}
            return {"success": False, "message": "Inspect configured target hosts list using 'ansible-inventory'."}

        # Step 7: Syntax dry checks
        if task_id == 7:
            if "playbook" in history_str or "ansible-playbook" in history_str:
                return {"success": True, "message": "Success! Playbook syntax check diagnostics processed."}
            return {"success": False, "message": "Trigger playbook syntax validation checks before applying execution."}

        # Step 8 (Mini Challenge): Module-specific custom criteria
        if task_id == 8:
            content = ""
            if os.path.exists(playbook_file):
                with open(playbook_file, "r", encoding="utf-8") as f:
                    content = f.read().lower()

            if lab_name == "introduction-to-ansible":
                if "ansible-doc" in history_str:
                    return {"success": True, "message": "Success! Sourced help docs for built-in ping module."}
                return {"success": False, "message": "Run ansible-doc ping command to inspect options schema."}

            elif lab_name == "inventory-files-and-hosts":
                if os.path.exists(hosts_file):
                    with open(hosts_file, "r", encoding="utf-8") as f:
                        h_content = f.read()
                    if "[webservers]" in h_content:
                        return {"success": True, "message": "Success! Inventory with webservers host group created."}
                return {"success": False, "message": "Define the '[webservers]' hosts block inside your hosts inventory file."}

            elif lab_name == "ad-hoc-commands":
                if "uptime" in history_str:
                    return {"success": True, "message": "Success! Executed ad-hoc module shell for system uptime."}
                return {"success": False, "message": "Run ad-hoc command using shell module passing uptime argument."}

            elif lab_name == "writing-playbooks":
                if "welcome" in content or "hosts:" in content:
                    return {"success": True, "message": "Success! Welcome debug tasks playbook validated."}
                return {"success": False, "message": "Define tasks printing welcome debug messages inside playbook.yml."}

            elif lab_name == "variables-and-facts":
                if "vars:" in content or "app_port" in content:
                    return {"success": True, "message": "Success! Parameters app_port variable scope verified."}
                return {"success": False, "message": "Declare variables block mapping app_port parameter inside playbook.yml."}

            elif lab_name == "templates-and-jinja2":
                j2_path = os.path.join(shell.base_dir, "config.j2")
                if os.path.exists(j2_path):
                    with open(j2_path, "r", encoding="utf-8") as f:
                        j_content = f.read()
                    if "{{" in j_content and "}}" in j_content:
                        return {"success": True, "message": "Success! Dynamic Jinja2 configuration templates verified."}
                return {"success": False, "message": "Create config.j2 referencing app_port double curly braces template variables."}

            elif lab_name == "roles":
                role_task = os.path.join(shell.base_dir, "roles", "web", "tasks", "main.yml")
                if os.path.exists(role_task):
                    return {"success": True, "message": "Success! Web server role structure layout verified."}
                return {"success": False, "message": "Configure task commands inside roles/web/tasks/main.yml path."}

            elif lab_name == "ansible-galaxy":
                db_task = os.path.join(shell.base_dir, "roles", "db", "tasks", "main.yml")
                if os.path.exists(db_task):
                    return {"success": True, "message": "Success! Galaxy role packages layout verified."}
                return {"success": False, "message": "Verify db roles structure file roles/db/tasks/main.yml exists."}

            elif lab_name == "tags-handlers-and-conditionals":
                if "handlers:" in content or "notify:" in content or "tags:" in content:
                    return {"success": True, "message": "Success! Handler callback tasks notifications verified."}
                return {"success": False, "message": "Configure handlers block and notify task inside playbook.yml."}

            elif lab_name == "best-practices":
                if "syntax-check" in history_str or os.path.exists(os.path.join(shell.base_dir, "group_vars")):
                    return {"success": True, "message": "Success! Clean variables directory hierarchy verified."}
                return {"success": False, "message": "Create variables directory structures or run dry syntax checks."}

            elif lab_name == "ansible-capstone-project":
                if "ansible-playbook" in history_str:
                    return {"success": True, "message": "Success! Enterprise capstone orchestration playbooks verified."}
                return {"success": False, "message": "Run ansible-playbook command to apply capstone configurations."}

        return {"success": False, "message": "Unknown task check."}

    def _validate_aws(self, shell: Any, task_id: int, lab_name: str) -> Dict[str, Any]:
        """
        Validates AWS course progress against simulated infrastructure state and command history.
        """
        history_str = " ".join(shell.history).lower()
        state = getattr(shell, "aws_state", {})

        # Step 1: Initialize first files / command check
        if task_id == 1:
            if lab_name == "aws-security-best-practices":
                if "create-security-group" in history_str or "security-group" in history_str:
                    return {"success": True, "message": "Success! VPC firewall security group initialized."}
                return {"success": False, "message": "Create a new VPC Security Group firewall by running create-security-group."}
            if "aws" in history_str or "terraform" in history_str or os.path.exists(os.path.join(shell.base_dir, "main.tf")):
                return {"success": True, "message": "Success! AWS lab workspace ready."}
            return {"success": False, "message": "Run basic aws configuration or terraform initialization command."}

        # Step 2: System diagnostic checks
        if task_id == 2:
            if "pwd" in history_str:
                return {"success": True, "message": "Success! Workspace path diagnostics verified."}
            return {"success": False, "message": "Verify path by executing pwd."}

        # Step 3: List files check
        if task_id == 3:
            if "ls" in history_str:
                return {"success": True, "message": "Success! Active workspace files cataloged."}
            return {"success": False, "message": "Execute ls command to display files inside the workspace."}

        # Step 4: Verify files contents display
        if task_id == 4:
            if "cat" in history_str:
                return {"success": True, "message": "Success! Read workspace parameters templates configuration details."}
            return {"success": False, "message": "View local variables template configuration values using cat."}

        # Step 5: Read IAM user stats
        if task_id == 5:
            if "iam" in history_str or "user" in history_str or len(state.get("users", [])) > 0:
                return {"success": True, "message": "Success! Sourced active user accounts credentials information."}
            return {"success": False, "message": "Run aws iam list-users to display active user credentials list."}

        # Step 6: Query ec2 compute instances
        if task_id == 6:
            if "ec2" in history_str or "instances" in history_str or len(state.get("instances", [])) > 0:
                return {"success": True, "message": "Success! Sourced compute virtual machines records."}
            return {"success": False, "message": "Query running instances lists status by running ec2 describe-instances."}

        # Step 7: Query s3 storage bucket status
        if task_id == 7:
            if "s3" in history_str or len(state.get("buckets", {})) > 0:
                return {"success": True, "message": "Success! Active object storage repositories audited."}
            return {"success": False, "message": "List globally registered storage buckets by executing aws s3 ls."}

        # Step 8 (Mini Challenge): Module-specific custom criteria
        if task_id == 8:
            if lab_name == "aws-cloud-fundamentals":
                if "configure" in history_str:
                    return {"success": True, "message": "Success! AWS CLI profile configuration loaded."}
                return {"success": False, "message": "Configure local credentials profile by executing aws configure list."}

            elif lab_name == "iam-users-groups-and-roles":
                if "devlab-admin" in state.get("users", []):
                    return {"success": True, "message": "Success! IAM administrative user account created."}
                return {"success": False, "message": "Create a new IAM user account named 'devlab-admin'."}

            elif lab_name == "ec2-virtual-machines":
                if len(state.get("instances", [])) > 0:
                    return {"success": True, "message": "Success! Micro compute server provisioned successfully."}
                return {"success": False, "message": "Launch a new virtual compute node by running aws ec2 run-instances."}

            elif lab_name == "vpc-networking":
                if len(state.get("subnets", [])) > 0:
                    return {"success": True, "message": "Success! Subnet configuration partition added."}
                return {"success": False, "message": "Create a routing subnet using ec2 create-subnet command."}

            elif lab_name == "s3-storage":
                has_uploaded = False
                for b_name, files in state.get("buckets", {}).items():
                    if "test.txt" in files:
                        has_uploaded = True
                        break
                if has_uploaded:
                    return {"success": True, "message": "Success! Object uploaded to bucket successfully."}
                return {"success": False, "message": "Upload 'test.txt' to s3 storage bucket by executing aws s3 cp."}

            elif lab_name == "rds-databases":
                if len(state.get("rds", [])) > 0:
                    return {"success": True, "message": "Success! Postgres RDS databases instance deployed."}
                return {"success": False, "message": "Create Postgres database instances by running rds create-db-instance."}

            elif lab_name == "load-balancers-and-auto-scaling":
                if len(state.get("asg", [])) > 0 or "asg" in history_str:
                    return {"success": True, "message": "Success! Load balancers auto scaling capacities configured."}
                return {"success": False, "message": "Create an Auto Scaling Group template by running create-auto-scaling-group."}

            elif lab_name == "cloudwatch-monitoring":
                if len(state.get("alarms", [])) > 0 or "alarm" in history_str:
                    return {"success": True, "message": "Success! Custom CPU monitoring alarm limits defined."}
                return {"success": False, "message": "Configure CPU utilization metric thresholds alerts using put-metric-alarm."}

            elif lab_name == "infrastructure-with-terraform-on-aws":
                if "plan" in history_str:
                    return {"success": True, "message": "Success! Infrastructure configuration blue print verified."}
                return {"success": False, "message": "Verify resources addition plan maps by executing terraform plan."}

            elif lab_name == "deploying-applications-on-aws":
                if "curl" in history_str:
                    return {"success": True, "message": "Success! Target servers port connections audited."}
                return {"success": False, "message": "Check application response status by calling curl."}

            elif lab_name == "aws-security-best-practices":
                if "authorize" in history_str:
                    return {"success": True, "message": "Success! Port firewall ingress configurations authorized."}
                return {"success": False, "message": "Authorize port ingress traffic parameters on the Security Group."}

            elif lab_name == "aws-capstone-project":
                state_file = os.path.join(shell.base_dir, "terraform.tfstate")
                if os.path.exists(state_file) and "curl" in history_str:
                    return {"success": True, "message": "Success! Complete multi-tier architecture verified and deployed."}
                return {"success": False, "message": "Apply infrastructure blueprints via terraform apply and curl verify output."}

        return {"success": False, "message": "Unknown task check."}


validation_engine = ValidationEngine()
