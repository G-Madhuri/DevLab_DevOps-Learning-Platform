import os
import shutil
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime
import docker
from app.core.config import settings

logger = logging.getLogger("app.services.runtime")


class SimulatedShell:
    """
    Simulates a Linux shell execution environment locally on the host.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", session_id)
        )
        self.student_home = os.path.join(self.base_dir, "home", "student")
        
        # Initialize virtual directory tree
        os.makedirs(self.student_home, exist_ok=True)
        os.makedirs(os.path.join(self.student_home, "drafts"), exist_ok=True)
        os.makedirs(os.path.join(self.student_home, "old_logs"), exist_ok=True)
        
        with open(os.path.join(self.student_home, "welcome.txt"), "w") as f:
            f.write("Welcome to DevLab Linux Basics! Use this interactive shell to practice your commands.\n")
        with open(os.path.join(self.student_home, ".bashrc"), "w") as f:
            f.write("# Simulated bash config file\n")
        with open(os.path.join(self.student_home, ".profile"), "w") as f:
            f.write("# Simulated profile config file\n")
            
        self.cwd = "/home/student"
        self.env = {
            "USER": "student",
            "HOME": "/home/student",
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "SHELL": "/bin/bash",
            "TERM": "xterm-256color",
        }
        self.permissions: Dict[str, str] = {}
        self.history = []

    def get_local_path(self, virtual_path: str) -> str:
        clean_vpath = virtual_path
        if clean_vpath.startswith("~"):
            clean_vpath = clean_vpath.replace("~", "/home/student", 1)
            
        if not clean_vpath.startswith("/"):
            clean_vpath = os.path.normpath(os.path.join(self.cwd, clean_vpath))
        else:
            clean_vpath = os.path.normpath(clean_vpath)
            
        clean_vpath = clean_vpath.replace("\\", "/")
            
        if not clean_vpath.startswith("/home/student"):
            clean_vpath = "/home/student"
            
        relative_part = clean_vpath.lstrip("/")
        return os.path.join(self.base_dir, relative_part)

    def execute_command(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""

        # Handle chained commands with &&
        if "&&" in cmd_line:
            parts_chained = [c.strip() for c in cmd_line.split("&&")]
            results = []
            for chained_cmd in parts_chained:
                if chained_cmd:
                    result = self.execute_command(chained_cmd)
                    results.append(result)
            # Return the last prompt (which includes the final prompt line)
            return results[-1] if results else ""

        self.history.append(cmd_line)
        parts = cmd_line.split()
        cmd = parts[0]
        args = parts[1:]

        def make_prompt(output_text: str = "") -> str:
            suffix = "\r\n" if output_text and not output_text.endswith("\r\n") else ""
            pwd_part = self.cwd.replace('/home/student', '')
            pwd_part = pwd_part if pwd_part else ""
            return f"{output_text}{suffix}student@devlab:~{pwd_part}$ "

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
            new_vpath = target
            if not target.startswith("/"):
                new_vpath = os.path.normpath(os.path.join(self.cwd, target))
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
                "--- ping statistics ---",
                "1 packets transmitted, 1 received, 0% packet loss"
            ]
            return make_prompt("\r\n".join(ping_lines))
        elif cmd == "ip":
            if args and args[0] == "route":
                return make_prompt("default via 172.17.0.1 dev eth0 proto dhcp src 172.17.0.2 metric 100")
            return make_prompt("ip route configurations")
        elif cmd == "ps":
            return make_prompt("  PID TTY          TIME CMD\r\n    1 pts/0    00:00:00 bash\r\n   42 pts/0    00:00:00 ps")
        elif cmd == "htop":
            return make_prompt("htop dashboard complete.")
        else:
            return make_prompt(f"bash: {cmd}: command not found")


class SimulatedDockerShell(SimulatedShell):
    """
    Subclass of SimulatedShell that emulates Docker command line operations.
    """
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.mock_containers: Dict[str, Any] = {}
        self.mock_volumes = []
        self.mock_networks = []
        self.mock_images = ["alpine", "hello-world", "nginx", "redis"]

    def execute_command(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""

        self.history.append(cmd_line)
        parts = cmd_line.split()
        cmd = parts[0]
        args = parts[1:]

        def make_prompt(output_text: str = "") -> str:
            suffix = "\r\n" if output_text and not output_text.endswith("\r\n") else ""
            pwd_part = self.cwd.replace('/home/student', '')
            return f"{output_text}{suffix}student@devlab:~{pwd_part}$ "

        if cmd == "docker":
            if not args:
                return make_prompt("Usage: docker [OPTIONS] COMMAND")
            sub = args[0]
            
            if sub == "--version":
                return make_prompt("Docker version 24.0.7, build afdd53b")
            elif sub == "info":
                return make_prompt("Kernel Version: 6.8.0-1002-aws\r\nOperating System: Ubuntu 24.04 LTS\r\nContainers: 1")
            elif sub == "run":
                name = "mock_container_" + secrets.token_hex(4)
                if "--name" in args:
                    idx = args.index("--name")
                    if idx + 1 < len(args):
                        name = args[idx+1]
                image = args[-1]
                self.mock_containers[name] = {"image": image, "status": "running", "id": secrets.token_hex(16)}
                if "hello-world" in image:
                    self.mock_containers[name]["status"] = "exited"
                    return make_prompt("Hello from Docker!\r\nThis message shows that your installation appears to be working correctly.")
                return make_prompt(self.mock_containers[name]["id"])
            elif sub == "ps":
                show_all = "-a" in args
                lines = ["CONTAINER ID   IMAGE         COMMAND                  CREATED         STATUS         PORTS     NAMES"]
                for c_name, c_info in self.mock_containers.items():
                    if show_all or c_info["status"] == "running":
                        lines.append(f"{c_info['id'][:12]}   {c_info['image'][:11]:<12} \"/entrypoint.sh\"        10 seconds ago  Up 10 seconds            {c_name}")
                return make_prompt("\r\n".join(lines))
            elif sub == "images":
                lines = [
                    "REPOSITORY      TAG       IMAGE ID       CREATED        SIZE",
                    "alpine          latest    05455a08881e   2 hours ago    7.38MB",
                    "nginx           latest    605c77e624dd   3 days ago     142MB",
                    "redis           latest    39005c77e62d   5 days ago     113MB",
                    "hello-world     latest    feb5d9ad7470   3 months ago   13kB",
                ]
                # Append user-built images from mock_images list
                for img in self.mock_images:
                    if ":" in img and img not in ["alpine", "hello-world", "nginx", "redis"]:
                        repo, tag_part = img.split(":", 1)
                        lines.append(f"{repo:<16}{tag_part:<10}1f2113ea1a0c   just now       12.1MB")
                return make_prompt("\r\n".join(lines))
            elif sub == "build":
                # Check if Dockerfile exists in current directory
                local_df = self.get_local_path(os.path.join(self.cwd, "Dockerfile"))
                if not os.path.exists(local_df):
                    return make_prompt(
                        "Error: failed to solve: failed to read dockerfile: "
                        "open Dockerfile: no such file or directory\r\n"
                        "Hint: Create a Dockerfile first using: echo \"FROM alpine\" > Dockerfile"
                    )
                # Parse the -t tag argument
                tag = "unnamed_image:latest"
                if "-t" in args:
                    idx = args.index("-t")
                    if idx + 1 < len(args):
                        tag = args[idx + 1]
                # Read Dockerfile contents for step count
                try:
                    with open(local_df, "r", encoding="utf-8", errors="ignore") as f:
                        df_lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
                except Exception:
                    df_lines = ["FROM alpine"]

                is_cached = tag in self.mock_images
                if not is_cached:
                    self.mock_images.append(tag)

                # Build realistic step-by-step output
                build_steps = []
                build_steps.append("Sending build context to Docker daemon  2.048kB")
                for i, step in enumerate(df_lines, start=1):
                    build_steps.append(f"Step {i}/{len(df_lines)} : {step}")
                    if is_cached:
                        build_steps.append(" ---> Using cache")
                        build_steps.append(" ---> 05455a08881e")
                    else:
                        if step.upper().startswith("FROM"):
                            build_steps.append(" ---> 05455a08881e")
                        else:
                            build_steps.append(" ---> Running in 9481ad12415d")
                            build_steps.append("Removing intermediate container 9481ad12415d")
                            build_steps.append(" ---> 1f2113ea1a0c")
                build_steps.append("Successfully built 1f2113ea1a0c")
                build_steps.append(f"Successfully tagged {tag}")
                return make_prompt("\r\n".join(build_steps))
            elif sub == "pull":
                image = args[1] if len(args) > 1 else "alpine"
                if image not in self.mock_images:
                    self.mock_images.append(image)
                pull_lines = [
                    f"Using default tag: latest",
                    f"latest: Pulling from library/{image}",
                    f"Digest: sha256:4c17c76a165842881efe88c0054a81816",
                    f"Status: Downloaded newer image for {image}:latest"
                ]
                return make_prompt("\r\n".join(pull_lines))
            elif sub == "volume":
                if len(args) > 1 and args[1] == "create":
                    v_name = args[2] if len(args) > 2 else "volume1"
                    self.mock_volumes.append(v_name)
                    return make_prompt(v_name)
                elif len(args) > 1 and args[1] == "ls":
                    lines = ["DRIVER    VOLUME NAME"]
                    for v in self.mock_volumes:
                        lines.append(f"local     {v}")
                    return make_prompt("\r\n".join(lines))
                return make_prompt("Usage: docker volume COMMAND")
            elif sub == "network":
                if len(args) > 1 and args[1] == "create":
                    n_name = args[2] if len(args) > 2 else "net1"
                    self.mock_networks.append(n_name)
                    return make_prompt(n_name)
                elif len(args) > 1 and args[1] == "ls":
                    lines = [
                        "NETWORK ID     NAME          DRIVER         SCOPE",
                        "112233445566   bridge        bridge         local"
                    ]
                    for n in self.mock_networks:
                        lines.append(f"a1b2c3d4e5f6   {n:<13} bridge         local")
                    return make_prompt("\r\n".join(lines))
                return make_prompt("Usage: docker network COMMAND")
            elif sub == "logs":
                c_name = args[1] if len(args) > 1 else ""
                if c_name in self.mock_containers:
                    return make_prompt("Starting nginx process...\r\nReady for HTTP requests on port 80.")
                return make_prompt(f"Error: No such container: {c_name}")
            elif sub == "exec":
                c_name = args[1] if len(args) > 1 else ""
                exec_cmd = " ".join(args[2:])
                if c_name in self.mock_containers:
                    if "date" in exec_cmd:
                        return make_prompt(datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y"))
                    return make_prompt("exec command completed.")
                return make_prompt(f"Error: No such container: {c_name}")
            elif sub == "inspect":
                resource = args[1] if len(args) > 1 else ""
                mock_id = "d3adb33f1a2c"
                mock_ip = "172.17.0.2"
                return make_prompt(
                    f'[\n'
                    f'  {{\n'
                    f'    "Id": "{mock_id}",\n'
                    f'    "Name": "/{resource}",\n'
                    f'    "State": {{"Status": "running", "Running": true}},\n'
                    f'    "NetworkSettings": {{"IPAddress": "{mock_ip}", "Gateway": "172.17.0.1"}},\n'
                    f'    "Mounts": [],\n'
                    f'    "Config": {{"Hostname": "{resource}", "Env": []}}\n'
                    f'  }}\n'
                    f']'
                )
            elif sub == "stop":
                c_name = args[1] if len(args) > 1 else ""
                if c_name in self.mock_containers:
                    self.mock_containers[c_name]["status"] = "exited"
                    return make_prompt(c_name)
                return make_prompt(f"Error: No such container: {c_name}")
            elif sub == "rm":
                c_name = args[1] if len(args) > 1 else ""
                # Allow removing exited containers
                if c_name in self.mock_containers:
                    self.mock_containers.pop(c_name)
                    return make_prompt(c_name)
                # If not found but was already removed, confirm silently
                return make_prompt(c_name)
            elif sub == "system":
                action = args[1] if len(args) > 1 else ""
                if action == "prune":
                    # Remove all exited containers
                    to_remove = [k for k, v in self.mock_containers.items() if v.get("status") == "exited"]
                    for k in to_remove:
                        self.mock_containers.pop(k)
                    freed = len(to_remove) * 142
                    return make_prompt(
                        f"WARNING! This will remove all stopped containers, unused networks, dangling images, and build cache.\r\n"
                        f"Deleted Containers: {len(to_remove)}\r\n"
                        f"Total reclaimed space: {freed}MB"
                    )
                return make_prompt(f"docker system: '{action}' is not a docker system command.")
            elif sub == "compose":
                return make_prompt("Creating network \"student_default\" with the default driver\r\nCreating student_web_1 ... done\r\nCreating student_db_1  ... done")
            else:
                return make_prompt(f"docker: '{sub}' is not a docker command.\r\nSee 'docker --help' for a list of available commands.")

        return super().execute_command(cmd_line)


# ── Modular Runtime Abstractions ─────────────────────

class BaseRuntime:
    """
    Polymorphic runtime driver interface.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        raise NotImplementedError()

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        raise NotImplementedError()


class LinuxRuntime(BaseRuntime):
    def __init__(self, docker_client: Optional[docker.DockerClient]):
        self.client = docker_client

    def create_session(self, session_id: str) -> Dict[str, Any]:
        if self.client:
            try:
                container = self.client.containers.run(
                    image="ubuntu:24.04",
                    command="/bin/bash",
                    name=f"devlab-sandbox-{session_id}",
                    stdin_open=True,
                    tty=True,
                    detach=True,
                    mem_limit="256m",
                    nano_cpus=500000000,
                )
                setup_cmds = [
                    "useradd -m -s /bin/bash student",
                    "echo 'student:student' | chpasswd",
                    "usermod -aG sudo student",
                    "mkdir -p /home/student/drafts /home/student/old_logs",
                    "echo 'Welcome to DevLab Linux Basics! Use this interactive shell to practice your commands.' > /home/student/welcome.txt",
                    "echo '# Bash config' > /home/student/.bashrc",
                    "echo '# Profile config' > /home/student/.profile",
                    "chown -R student:student /home/student"
                ]
                for cmd in setup_cmds:
                    container.exec_run(cmd, user="root")
                return {"container_id": container.id, "status": "running", "mode": "docker"}
            except Exception as e:
                logger.error(f"LinuxRuntime failed to launch container: {e}. Falling back.")
        
        # Local simulation
        return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        if self.client and container_id and not container_id.startswith("simulated-"):
            try:
                container = self.client.containers.get(container_id)
                container.stop(timeout=2)
                container.remove()
            except Exception as e:
                logger.warn(f"Failed to stop Linux container: {e}")


class DockerRuntime(BaseRuntime):
    """
    Docker runtime provisioner implementing nested Docker capabilities.
    """
    def __init__(self, docker_client: Optional[docker.DockerClient]):
        self.client = docker_client

    def create_session(self, session_id: str) -> Dict[str, Any]:
        if self.client:
            try:
                # Mount host docker socket to enable nested Docker operations
                container = self.client.containers.run(
                    image="ubuntu:24.04",
                    command="/bin/bash",
                    name=f"devlab-sandbox-{session_id}",
                    stdin_open=True,
                    tty=True,
                    detach=True,
                    mem_limit="512m",  # Increase resources for docker runs
                    volumes={
                        "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"}
                    }
                )
                # 1. Setup student user immediately (synchronously, very fast)
                fast_setup = [
                    "useradd -m -s /bin/bash student",
                    "echo 'student:student' | chpasswd",
                    "usermod -aG sudo student",
                    "mkdir -p /home/student",
                    "chown -R student:student /home/student"
                ]
                for cmd in fast_setup:
                    container.exec_run(cmd, user="root")

                # 2. Install docker client in background (asynchronously, won't block launch)
                install_cmd = "sh -c 'apt-get update && apt-get install -y docker.io && usermod -aG docker student'"
                container.exec_run(install_cmd, user="root", detach=True)

                return {"container_id": container.id, "status": "running", "mode": "docker"}
            except Exception as e:
                logger.error(f"DockerRuntime failed to launch nested container: {e}. Falling back.")

        # Local simulation
        return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        if self.client and container_id and not container_id.startswith("simulated-"):
            try:
                container = self.client.containers.get(container_id)
                container.stop(timeout=2)
                container.remove()
            except Exception as e:
                logger.warn(f"Failed to stop Docker container: {e}")


# ── Global Coordinator Service ────────────────────────

class LabRuntimeService:
    def __init__(self):
        self.simulated_sessions: Dict[str, SimulatedShell] = {}
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            self.is_docker_available = True
        except Exception:
            self.is_docker_available = False
            self.docker_client = None

        self.linux_runtime = LinuxRuntime(self.docker_client)
        self.docker_runtime = DockerRuntime(self.docker_client)

    def create_lab(self, session_id: str, lab_name: str = "linux-basics") -> Dict[str, Any]:
        """
        Delegates lab initialization checks to custom Runtimes.
        """
        if "docker" in lab_name:
            res = self.docker_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedDockerShell(session_id)
            return res
        else:
            res = self.linux_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            return res

    def stop_lab(self, session_id: str, container_id: Optional[str] = None, lab_name: str = "linux-basics") -> None:
        """
        Cleans up container sessions and directories.
        """
        if session_id in self.simulated_sessions:
            shell = self.simulated_sessions.pop(session_id)
            if os.path.exists(shell.base_dir):
                try:
                    shutil.rmtree(shell.base_dir)
                except Exception as e:
                    logger.warn(f"Failed to remove directory {shell.base_dir}: {e}")

        if "docker" in lab_name:
            self.docker_runtime.stop_session(session_id, container_id)
        else:
            self.linux_runtime.stop_session(session_id, container_id)

    def get_session_shell(self, session_id: str, lab_name: Optional[str] = None) -> Optional[SimulatedShell]:
        if session_id in self.simulated_sessions:
            return self.simulated_sessions[session_id]
        if lab_name:
            if "docker" in lab_name:
                shell = SimulatedDockerShell(session_id)
            else:
                shell = SimulatedShell(session_id)
            self.simulated_sessions[session_id] = shell
            return shell
        return None


# Global instance
runtime_service = LabRuntimeService()
