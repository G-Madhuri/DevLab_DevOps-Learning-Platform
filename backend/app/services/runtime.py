import os
import shutil
import logging
import secrets
from typing import Optional, Dict, Any
import docker
from app.core.config import settings

logger = logging.getLogger("app.services.runtime")


class SimulatedShell:
    """
    Simulates a Linux shell execution environment locally on the host.
    Creates a dedicated folder under scratch/sessions/{session_id}/home/student
    and interprets basic bash commands to return Linux-like standard output.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        # Workspace base directory
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", session_id)
        )
        self.student_home = os.path.join(self.base_dir, "home", "student")
        
        # Initialize virtual directory tree
        os.makedirs(self.student_home, exist_ok=True)
        
        # Track session current directory
        self.cwd = "/home/student"
        # Simulated environment variables
        self.env = {
            "USER": "student",
            "HOME": "/home/student",
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "SHELL": "/bin/bash",
            "TERM": "xterm-256color",
        }
        # Simulated permissions registry
        self.permissions: Dict[str, str] = {}
        # Command history log
        self.history = []

    def get_local_path(self, virtual_path: str) -> str:
        """
        Converts a virtual bash path (e.g. /home/student/projects)
        into a real path on the host system.
        """
        clean_vpath = virtual_path
        if clean_vpath.startswith("~"):
            clean_vpath = clean_vpath.replace("~", "/home/student", 1)
            
        if not clean_vpath.startswith("/"):
            # Resolve relative to cwd
            clean_vpath = os.path.normpath(os.path.join(self.cwd, clean_vpath))
        else:
            clean_vpath = os.path.normpath(clean_vpath)
            
        # Standardize to forward slashes for cross-platform prefix checks
        clean_vpath = clean_vpath.replace("\\", "/")
            
        # Prevent path traversals outside base directory
        if not clean_vpath.startswith("/home/student"):
            clean_vpath = "/home/student"
            
        # Resolve to host system disk path
        relative_part = clean_vpath.lstrip("/")
        return os.path.join(self.base_dir, relative_part)

    def execute_command(self, cmd_line: str) -> str:
        """
        Parses and emulates standard Linux commands.
        """
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""
        
        self.history.append(cmd_line)
        parts = cmd_line.split()
        cmd = parts[0]
        args = parts[1:]

        # Emulated prompt return utility
        def make_prompt(output_text: str = "") -> str:
            suffix = "\r\n" if output_text and not output_text.endswith("\r\n") else ""
            return f"{output_text}{suffix}student@devlab:~{self.cwd.replace('/home/student', '')}$ "

        if cmd == "pwd":
            return make_prompt(self.cwd)

        elif cmd == "clear":
            return "\033[H\033[2J" + make_prompt()

        elif cmd == "whoami":
            return make_prompt("student")

        elif cmd == "id":
            return make_prompt("uid=1000(student) gid=1000(student) groups=1000(student),27(sudo)")

        elif cmd == "groups":
            return make_prompt("student sudo")

        elif cmd == "hostname":
            return make_prompt("devlab-linux-sandbox")

        elif cmd == "cd":
            target = args[0] if args else "/home/student"
            if target == "~":
                target = "/home/student"
            
            # Resolve target path
            new_vpath = target
            if not target.startswith("/"):
                new_vpath = os.path.normpath(os.path.join(self.cwd, target))
            
            # Prevent going above home
            if not new_vpath.startswith("/home/student"):
                new_vpath = "/home/student"
                
            local_target = self.get_local_path(new_vpath)
            if os.path.exists(local_target) and os.path.isdir(local_target):
                self.cwd = new_vpath.replace("\\", "/")
                return make_prompt()
            else:
                return make_prompt(f"cd: no such file or directory: {target}")

        elif cmd == "ls":
            show_all = "-a" in args
            local_cwd = self.get_local_path(self.cwd)
            try:
                files = os.listdir(local_cwd)
                if not show_all:
                    files = [f for f in files if not f.startswith(".")]
                
                # Standard spacing
                output = "  ".join(files)
                return make_prompt(output)
            except Exception as e:
                return make_prompt(f"ls: cannot open directory: {e}")

        elif cmd == "mkdir":
            if not args:
                return make_prompt("mkdir: missing operand")
            target = args[0]
            local_path = self.get_local_path(os.path.join(self.cwd, target))
            try:
                os.makedirs(local_path, exist_ok=True)
                return make_prompt()
            except Exception as e:
                return make_prompt(f"mkdir: cannot create directory '{target}': {e}")

        elif cmd == "touch":
            if not args:
                return make_prompt("touch: missing file operand")
            target = args[0]
            local_path = self.get_local_path(os.path.join(self.cwd, target))
            try:
                with open(local_path, "a"):
                    os.utime(local_path, None)
                return make_prompt()
            except Exception as e:
                return make_prompt(f"touch: cannot create file '{target}': {e}")

        elif cmd == "cat":
            if not args:
                return make_prompt("cat: missing file operand")
            target = args[0]
            local_path = self.get_local_path(os.path.join(self.cwd, target))
            if os.path.exists(local_path) and os.path.isfile(local_path):
                try:
                    with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                        return make_prompt(f.read())
                except Exception as e:
                    return make_prompt(f"cat: read error: {e}")
            else:
                return make_prompt(f"cat: {target}: No such file or directory")

        elif cmd == "echo":
            # Very basic redirect emulator: echo "text" > file
            if ">" in args:
                idx = args.index(">")
                text = " ".join(args[:idx]).strip('"\'')
                dest_file = args[idx+1]
                local_path = self.get_local_path(os.path.join(self.cwd, dest_file))
                try:
                    with open(local_path, "w", encoding="utf-8") as f:
                        f.write(text + "\n")
                    return make_prompt()
                except Exception as e:
                    return make_prompt(f"echo: redirect write error: {e}")
            elif ">>" in args:
                idx = args.index(">>")
                text = " ".join(args[:idx]).strip('"\'')
                dest_file = args[idx+1]
                local_path = self.get_local_path(os.path.join(self.cwd, dest_file))
                try:
                    with open(local_path, "a", encoding="utf-8") as f:
                        f.write(text + "\n")
                    return make_prompt()
                except Exception as e:
                    return make_prompt(f"echo: redirect append error: {e}")
            else:
                text = " ".join(args).strip('"\'')
                return make_prompt(text)

        elif cmd == "rm":
            recursive = "-r" in args or "-rf" in args
            clean_args = [a for a in args if not a.startswith("-")]
            if not clean_args:
                return make_prompt("rm: missing operand")
            target = clean_args[0]
            local_path = self.get_local_path(os.path.join(self.cwd, target))
            if os.path.exists(local_path):
                try:
                    if os.path.isdir(local_path):
                        if recursive:
                            shutil.rmtree(local_path)
                        else:
                            return make_prompt(f"rm: cannot remove '{target}': Is a directory")
                    else:
                        os.remove(local_path)
                    return make_prompt()
                except Exception as e:
                    return make_prompt(f"rm: remove error: {e}")
            else:
                return make_prompt() if "-f" in args else make_prompt(f"rm: cannot remove '{target}': No such file or directory")

        elif cmd == "cp":
            clean_args = [a for a in args if not a.startswith("-")]
            if len(clean_args) < 2:
                return make_prompt("cp: missing file operand")
            src, dest = clean_args[0], clean_args[1]
            local_src = self.get_local_path(os.path.join(self.cwd, src))
            local_dest = self.get_local_path(os.path.join(self.cwd, dest))
            
            if not os.path.exists(local_src):
                return make_prompt(f"cp: cannot stat '{src}': No such file or directory")
                
            try:
                if os.path.isdir(local_src):
                    if os.path.exists(local_dest):
                        local_dest = os.path.join(local_dest, os.path.basename(local_src))
                    shutil.copytree(local_src, local_dest)
                else:
                    if os.path.isdir(local_dest):
                        local_dest = os.path.join(local_dest, os.path.basename(local_src))
                    shutil.copy2(local_src, local_dest)
                return make_prompt()
            except Exception as e:
                return make_prompt(f"cp: copy error: {e}")

        elif cmd == "mv":
            if len(args) < 2:
                return make_prompt("mv: missing destination file operand")
            src, dest = args[0], args[1]
            local_src = self.get_local_path(os.path.join(self.cwd, src))
            local_dest = self.get_local_path(os.path.join(self.cwd, dest))
            
            if not os.path.exists(local_src):
                return make_prompt(f"mv: cannot stat '{src}': No such file or directory")
                
            try:
                if os.path.isdir(local_dest):
                    local_dest = os.path.join(local_dest, os.path.basename(local_src))
                shutil.move(local_src, local_dest)
                return make_prompt()
            except Exception as e:
                return make_prompt(f"mv: move error: {e}")

        elif cmd == "chmod":
            if len(args) < 2:
                return make_prompt("chmod: missing operand")
            perms, target = args[0], args[1]
            local_path = self.get_local_path(os.path.join(self.cwd, target))
            if os.path.exists(local_path):
                self.permissions[target] = perms
                return make_prompt()
            else:
                return make_prompt(f"chmod: cannot access '{target}': No such file or directory")

        elif cmd == "grep":
            if len(args) < 2:
                return make_prompt("grep: missing search parameters")
            pattern = args[0].strip('"\'')
            target = args[1]
            local_path = self.get_local_path(os.path.join(self.cwd, target))
            if os.path.exists(local_path) and os.path.isfile(local_path):
                try:
                    with open(local_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    matches = [l.strip() for l in lines if pattern in l]
                    return make_prompt("\r\n".join(matches))
                except Exception as e:
                    return make_prompt(f"grep: read error: {e}")
            else:
                return make_prompt(f"grep: {target}: No such file or directory")

        elif cmd == "export":
            if args:
                eq_part = args[0].split("=")
                if len(eq_part) == 2:
                    self.env[eq_part[0]] = eq_part[1].strip('"\'')
            return make_prompt()

        elif cmd == "env" or cmd == "printenv":
            env_lines = [f"{k}={v}" for k, v in self.env.items()]
            return make_prompt("\r\n".join(env_lines))

        elif cmd == "ping":
            if not args:
                return make_prompt("ping: missing host operand")
            host = args[0]
            ping_lines = [
                f"PING {host} (127.0.0.1) 56(84) bytes of data.",
                f"64 bytes from {host} (127.0.0.1): icmp_seq=1 ttl=64 time=0.035 ms",
                f"64 bytes from {host} (127.0.0.1): icmp_seq=2 ttl=64 time=0.042 ms",
                f"--- {host} ping statistics ---",
                "2 packets transmitted, 2 received, 0% packet loss, time 1003ms"
            ]
            return make_prompt("\r\n".join(ping_lines))

        elif cmd == "ip":
            if args and args[0] == "route":
                route_lines = [
                    "default via 172.17.0.1 dev eth0 proto dhcp src 172.17.0.2 metric 100",
                    "172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.2"
                ]
                return make_prompt("\r\n".join(route_lines))
            return make_prompt("Usage: ip [ OPTIONS ] OBJECT { COMMAND | help }")

        elif cmd == "ps":
            ps_lines = [
                "  PID TTY          TIME CMD",
                "    1 pts/0    00:00:00 bash",
                "   42 pts/0    00:00:00 ps"
            ]
            return make_prompt("\r\n".join(ps_lines))

        elif cmd == "htop":
            htop_lines = [
                "  1  [||                                     3.2%]   Tasks: 4, 1 thr; 1 running",
                "  Mem[|||||||||                        256M/2.00G]   Load average: 0.05 0.12 0.08",
                "  Swp[                                    0K/0K ]",
                "  PID USER      PRI  NI  VIRT   RES   SHR S CPU% MEM%   TIME+  Command",
                "    1 student    20   0  8212  3812  2104 S  0.0  0.2  0:00.08 /bin/bash",
                "   12 student    20   0 12040  4212  2408 R  1.2  0.2  0:00.02 htop"
            ]
            return make_prompt("\r\n".join(htop_lines))

        else:
            return make_prompt(f"bash: {cmd}: command not found")


class LabRuntimeService:
    def __init__(self):
        # Local cache for active simulated terminal sessions
        self.simulated_sessions: Dict[str, SimulatedShell] = {}
        
        # Safe Docker Client initializations
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            self.is_docker_available = True
            logger.info("Docker daemon successfully detected. Production containers active.")
        except Exception as e:
            self.is_docker_available = False
            self.docker_client = None
            logger.warn(f"Docker connection failed ({e}). Bootstrapping locally in Simulated Terminal mode.")

    def create_lab(self, session_id: str, image_name: str = "ubuntu:24.04") -> Dict[str, Any]:
        """
        Creates and starts an isolated learning lab.
        Returns details of container metadata.
        """
        if self.is_docker_available and self.docker_client:
            try:
                logger.info(f"Launching Docker container for session {session_id}...")
                # Run isolated container with student user and limits
                container = self.docker_client.containers.run(
                    image=image_name,
                    command="/bin/bash",
                    name=f"devlab-sandbox-{session_id}",
                    stdin_open=True,
                    tty=True,
                    detach=True,
                    mem_limit="256m",  # Restrict memory limits for security
                    nano_cpus=500000000, # 0.5 CPU limit
                    network_mode="bridge",
                )
                
                # Setup student user structure inside the live container
                setup_cmds = [
                    "useradd -m -s /bin/bash student",
                    "echo 'student:student' | chpasswd",
                    "usermod -aG sudo student",
                    "mkdir -p /home/student",
                    "chown -R student:student /home/student"
                ]
                for cmd in setup_cmds:
                    container.exec_run(cmd, user="root")

                return {
                    "container_id": container.id,
                    "status": "running",
                    "mode": "docker",
                }
            except Exception as e:
                logger.error(f"Failed to spin up Docker container: {e}. Falling back to Simulated mode.")
                # Fallback to simulated if run fails
                
        # Simulated shell allocation
        logger.info(f"Provisioning in-memory Simulated Terminal for session {session_id}...")
        shell = SimulatedShell(session_id)
        self.simulated_sessions[session_id] = shell
        return {
            "container_id": f"simulated-{session_id}",
            "status": "running",
            "mode": "simulated",
        }

    def stop_lab(self, session_id: str, container_id: Optional[str] = None) -> None:
        """
        Stops and cleans up the active container or simulated directories.
        """
        # Clean up simulated shell context if exists
        if session_id in self.simulated_sessions:
            logger.info(f"Removing simulated terminal directories for {session_id}...")
            shell = self.simulated_sessions.pop(session_id)
            if os.path.exists(shell.base_dir):
                try:
                    shutil.rmtree(shell.base_dir)
                except Exception as e:
                    logger.warn(f"Failed to remove directory {shell.base_dir}: {e}")

        # Clean up docker container
        if self.is_docker_available and self.docker_client and container_id:
            if not container_id.startswith("simulated-"):
                try:
                    logger.info(f"Stopping & destroying Docker container {container_id}...")
                    container = self.docker_client.containers.get(container_id)
                    container.stop(timeout=2)
                    container.remove()
                except Exception as e:
                    logger.warn(f"Failed to stop/remove Docker container {container_id}: {e}")

    def get_session_shell(self, session_id: str) -> Optional[SimulatedShell]:
        """
        Retrieve active simulated shell by session ID.
        """
        return self.simulated_sessions.get(session_id)


# Global instance
runtime_service = LabRuntimeService()
