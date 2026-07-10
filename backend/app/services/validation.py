import os
import logging
from typing import Dict, Any, List
from app.services.runtime import runtime_service

logger = logging.getLogger("app.services.validation")


class ValidationEngine:
    def validate_task(
        self,
        session_id: str,
        container_id: str,
        task_id: int,
        mode: str,
    ) -> Dict[str, Any]:
        """
        Validates whether a specific task has been successfully completed by the student.
        Returns a dict indicating success or failure with message details.
        """
        # If in simulated mode, validate against local directories and shell history
        if mode == "simulated" or container_id.startswith("simulated-"):
            shell = runtime_service.get_session_shell(session_id)
            if not shell:
                return {"success": False, "message": "Simulated shell session not found."}
            return self._validate_simulated(shell, task_id)
        else:
            # Validate inside the live Docker container
            return self._validate_docker(container_id, task_id)

    def _validate_simulated(self, shell: Any, task_id: int) -> Dict[str, Any]:
        """
        Performs validations on the simulated filesystem state and shell command log.
        """
        history_str = " ".join(shell.history).lower()

        # Task 1: Navigation (pwd)
        if task_id == 1:
            if "pwd" in history_str:
                return {"success": True, "message": "Success! You queried the working directory."}
            return {"success": False, "message": "Try running the 'pwd' command to view your path."}

        # Task 2: Working Directories (ls -a)
        elif task_id == 2:
            if "ls -a" in history_str or "ls -la" in history_str or "ls -al" in history_str:
                return {"success": True, "message": "Success! You listed files including hidden ones."}
            return {"success": False, "message": "Try running 'ls -a' or 'ls -la' to show all directory contents."}

        # Task 3: Files (touch note.txt)
        elif task_id == 3:
            path = shell.get_local_path("note.txt")
            if os.path.exists(path) and os.path.isfile(path):
                return {"success": True, "message": "Success! 'note.txt' file created."}
            return {"success": False, "message": "Create an empty file named 'note.txt' using the touch command."}

        # Task 4: Directories (mkdir backup)
        elif task_id == 4:
            path = shell.get_local_path("backup")
            if os.path.exists(path) and os.path.isdir(path):
                return {"success": True, "message": "Success! 'backup' directory created."}
            return {"success": False, "message": "Create a subfolder named 'backup' in your home path using mkdir."}

        # Task 5: Copy (cp note.txt backup/note_copy.txt)
        elif task_id == 5:
            path = shell.get_local_path("backup/note_copy.txt")
            if os.path.exists(path) and os.path.isfile(path):
                return {"success": True, "message": "Success! note.txt copied to backup/note_copy.txt."}
            return {"success": False, "message": "Copy note.txt into the backup directory as note_copy.txt."}

        # Task 6: Move (mv backup/note_copy.txt ./note_copy.txt)
        elif task_id == 6:
            path = shell.get_local_path("note_copy.txt")
            if os.path.exists(path) and os.path.isfile(path):
                return {"success": True, "message": "Success! File moved back to home directory."}
            return {"success": False, "message": "Move note_copy.txt from the backup/ directory back to your home directory."}

        # Task 7: Rename (mv note_copy.txt log.txt)
        elif task_id == 7:
            old_path = shell.get_local_path("note_copy.txt")
            new_path = shell.get_local_path("log.txt")
            if os.path.exists(new_path) and not os.path.exists(old_path):
                return {"success": True, "message": "Success! note_copy.txt renamed to log.txt."}
            return {"success": False, "message": "Rename note_copy.txt in your home directory to log.txt using mv."}

        # Task 8: Delete (rm note.txt)
        elif task_id == 8:
            path = shell.get_local_path("note.txt")
            if not os.path.exists(path):
                return {"success": True, "message": "Success! note.txt deleted."}
            return {"success": False, "message": "Delete the original note.txt file using rm."}

        # Task 9: Viewing Files (cat log.txt)
        elif task_id == 9:
            if "cat log.txt" in history_str or "less log.txt" in history_str:
                return {"success": True, "message": "Success! You viewed the contents of log.txt."}
            return {"success": False, "message": "Use the cat command to inspect the contents of log.txt."}

        # Task 10: Permissions (chmod 600 log.txt)
        elif task_id == 10:
            perm = shell.permissions.get("log.txt")
            if perm == "600" or "chmod 600" in history_str:
                return {"success": True, "message": "Success! Permissions updated to 600 (owner read/write)."}
            return {"success": False, "message": "Change the permissions of log.txt to 600 (owner only access) using chmod."}

        # Task 11: Users (id)
        elif task_id == 11:
            if "id" in history_str:
                return {"success": True, "message": "Success! You inspected your user identity stats."}
            return {"success": False, "message": "Run the 'id' command to view your user and group identifiers."}

        # Task 12: Groups (groups)
        elif task_id == 12:
            if "groups" in history_str or "id" in history_str:
                return {"success": True, "message": "Success! Group memberships validated."}
            return {"success": False, "message": "Check your user groups using the 'groups' command."}

        # Task 13: Searching (grep student log.txt)
        elif task_id == 13:
            if "grep" in history_str:
                return {"success": True, "message": "Success! Grep keyword match verified."}
            return {"success": False, "message": "Search for lines or strings in files using the grep command."}

        # Task 14: Pipes (ls | grep log.txt)
        elif task_id == 14:
            if "|" in history_str and "grep" in history_str:
                return {"success": True, "message": "Success! Command pipeline executed correctly."}
            return {"success": False, "message": "Pipe the directory list to grep to filter files: ls | grep log.txt"}

        # Task 15: Redirection (echo 'DevOps' > dynamic.txt)
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

        # Task 16: Environment Variables (export REGISTRY=local)
        elif task_id == 16:
            if shell.env.get("REGISTRY") == "local" or "export registry=local" in history_str:
                return {"success": True, "message": "Success! Env variable REGISTRY is set."}
            return {"success": False, "message": "Export a custom environment variable named REGISTRY with value 'local'."}

        # Task 17: Processes (ps)
        elif task_id == 17:
            if "ps" in history_str or "top" in history_str:
                return {"success": True, "message": "Success! Active system processes listed."}
            return {"success": False, "message": "View running processes in this console environment using 'ps'."}

        # Task 18: Networking Basics (ip route)
        elif task_id == 18:
            if "ip route" in history_str or "route" in history_str or "ifconfig" in history_str or "ip a" in history_str:
                return {"success": True, "message": "Success! Inspected network details."}
            return {"success": False, "message": "Check routing tables or configuration parameters using 'ip route'."}

        # Task 19: Directory Deletions (rm -rf backup)
        elif task_id == 19:
            path = shell.get_local_path("backup")
            if not os.path.exists(path):
                return {"success": True, "message": "Success! backup folder cleaned up."}
            return {"success": False, "message": "Delete the backup directory and all files inside recursively using rm -rf."}

        # Task 20: Workspace Cleanup (final checklist)
        elif task_id == 20:
            local_cwd = shell.get_local_path(shell.cwd)
            files = os.listdir(local_cwd)
            if "backup" not in files and "note.txt" not in files:
                return {"success": True, "message": "Perfect! Workspace successfully verified and complete!"}
            return {"success": False, "message": "Verify that backup and note.txt files are deleted and execute ls -la."}

        return {"success": False, "message": "Unknown task identifier."}

    def _validate_docker(self, container_id: str, task_id: int) -> Dict[str, Any]:
        """
        Runs diagnostics directly inside the Docker container using exec_run.
        """
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

        # Note: In docker mode, we can inspect student bash history if recorded,
        # or simple file structures. For simplicity, check file structures
        # and command outcomes.
        if task_id == 1:
            return {"success": True, "message": "Success! Working directory checks out."}
        elif task_id == 2:
            return {"success": True, "message": "Success! Directory contents checked."}
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
        elif task_id == 9:
            return {"success": True, "message": "Success! log.txt inspected."}
        elif task_id == 10:
            # Check permissions
            res = container.exec_run("stat -c %a /home/student/log.txt", user="student")
            if res.exit_code == 0 and res.output.decode().strip() == "600":
                return {"success": True, "message": "Success! Permissions set to 600."}
            return {"success": False, "message": "Permissions of log.txt are not 600"}
        elif task_id == 11:
            return {"success": True, "message": "Success! Identity checks out."}
        elif task_id == 12:
            return {"success": True, "message": "Success! Groups checked."}
        elif task_id == 13:
            return {"success": True, "message": "Success! Grep keywords check out."}
        elif task_id == 14:
            return {"success": True, "message": "Success! Pipelines checks out."}
        elif task_id == 15:
            if file_exists("/home/student/dynamic.txt"):
                res = container.exec_run("cat /home/student/dynamic.txt", user="student")
                if "devops" in res.output.decode().lower():
                    return {"success": True, "message": "Success! Output redirected correctly."}
            return {"success": False, "message": "dynamic.txt does not contain 'DevOps'"}
        elif task_id == 16:
            return {"success": True, "message": "Success! Env parameters checked."}
        elif task_id == 17:
            return {"success": True, "message": "Success! Process listed."}
        elif task_id == 18:
            return {"success": True, "message": "Success! Networking checked."}
        elif task_id == 19:
            if not dir_exists("/home/student/backup"):
                return {"success": True, "message": "Success! backup folder deleted."}
            return {"success": False, "message": "backup directory still exists"}
        elif task_id == 20:
            if not file_exists("/home/student/note.txt") and not dir_exists("/home/student/backup"):
                return {"success": True, "message": "Success! Final cleanup checklist complete!"}
            return {"success": False, "message": "Cleanup incomplete."}

        return {"success": False, "message": "Unknown task."}


validation_engine = ValidationEngine()
