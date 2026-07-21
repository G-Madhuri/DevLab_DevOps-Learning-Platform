import os
import shutil
import logging
import secrets
import subprocess
from typing import Optional, Dict, Any
from datetime import datetime
import docker
from app.core.config import settings

logger = logging.getLogger("app.services.runtime")

try:
    from kubernetes import client as k8s_client, config as k8s_config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False



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

    
    def run_bash_script(self, script_path: str, script_args: list = []) -> str:
        if not os.path.exists(script_path):
            return f"bash: {os.path.basename(script_path)}: No such file or directory"
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return f"bash: error reading script: {e}"

        lines = content.splitlines()
        output_lines = []
        variables = {**self.env}
        
        # Add positional parameters
        for i, val in enumerate(script_args, start=1):
            variables[str(i)] = val
        variables["#"] = str(len(script_args))
        variables["@"] = " ".join(script_args)
        variables["?"] = "0"
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Simple variables expansion
            for k, v in list(variables.items()):
                line = line.replace(f"${k}", v)
                
            # Handle variable declarations
            if "=" in line and not line.startswith("if") and not line.startswith("while") and not line.startswith("["):
                parts = line.split("=", 1)
                var_name = parts[0].strip()
                var_val = parts[1].strip().strip('"\'')
                variables[var_name] = var_val
                continue
                
            if line.startswith("echo "):
                val = line[5:].strip().strip('"\'')
                output_lines.append(val)
            elif line == "pwd":
                output_lines.append(self.cwd)
            elif line.startswith("cd "):
                self.execute_command(line)
            else:
                res = self.execute_command(line)
                if res:
                    prompt_marker = "student@devlab:~"
                    if prompt_marker in res:
                        res = res.split(prompt_marker)[0].strip()
                    output_lines.append(res)
                    
        return "\r\n".join(output_lines)

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
            recursive = "-R" in args
            clean_args = [a for a in args if a != "-R"]
            if len(clean_args) < 2:
                return make_prompt("chmod: missing operand")
            perms, target = clean_args[0], clean_args[1]
            local_path = self.get_local_path(os.path.join(self.cwd, target))
            if os.path.exists(local_path):
                rel_target = os.path.relpath(local_path, self.base_dir).replace("\\", "/")
                self.permissions[rel_target] = perms
                if recursive and os.path.isdir(local_path):
                    for root, dirs, files in os.walk(local_path):
                        for d in dirs:
                            p_dir = os.path.relpath(os.path.join(root, d), self.base_dir).replace("\\", "/")
                            self.permissions[p_dir] = perms
                        for f in files:
                            p_file = os.path.relpath(os.path.join(root, f), self.base_dir).replace("\\", "/")
                            self.permissions[p_file] = perms
                return make_prompt()
            else:
                return make_prompt(f"chmod: cannot access '{target}': No such file or directory")
        elif cmd == "bash" or cmd.startswith("./"):
            script_name = args[0] if (cmd == "bash" and args) else cmd
            if script_name.startswith("./"):
                script_name = script_name[2:]
            
            rel_path = os.path.relpath(self.get_local_path(os.path.join(self.cwd, script_name)), self.base_dir).replace("\\", "/")
            if cmd.startswith("./"):
                perm = self.permissions.get(rel_path, "")
                if "x" not in perm and "7" not in perm and "5" not in perm:
                    return make_prompt(f"bash: ./{script_name}: Permission denied")
            
            local_path = self.get_local_path(os.path.join(self.cwd, script_name))
            script_args = args[1:] if cmd == "bash" else args
            if os.path.exists(local_path) and os.path.isfile(local_path):
                output = self.run_bash_script(local_path, script_args)
                return make_prompt(output)
            else:
                return make_prompt(f"bash: {script_name}: No such file or directory")
        elif cmd in ["ss", "netstat"]:
            return make_prompt(
                "State      Recv-Q Send-Q Local Address:Port               Peer Address:Port\r\n"
                "LISTEN     0      128    0.0.0.0:80                       0.0.0.0:*\r\n"
                "LISTEN     0      128    0.0.0.0:8080                     0.0.0.0:*\r\n"
                "LISTEN     0      128       [::]:80                          [::]:*\r\n"
                "LISTEN     0      128       [::]:8080                        [::]:*"
            )
        elif cmd in ["dig", "nslookup"]:
            domain = args[0] if args else "google.com"
            return make_prompt(
                f";; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 42183\r\n"
                f";; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1\r\n\r\n"
                f";; QUESTION SECTION:\r\n"
                f";{domain}.        IN  A\r\n\r\n"
                f";; ANSWER SECTION:\r\n"
                f"{domain}.  300 IN  A  142.250.190.46\r\n\r\n"
                f";; Query time: 14 msec\r\n"
                f";; SERVER: 127.0.0.11#53(127.0.0.11)"
            )
        elif cmd in ["curl", "wget"]:
            is_headers = "-I" in args or "-i" in args
            return make_prompt(
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=UTF-8\r\n"
                "Server: gws\r\n"
                "Content-Length: 21971\r\n"
                "Connection: close" if is_headers else "<!doctype html><html><head><title>Google</title></head><body>Hello</body></html>"
            )
        elif cmd in ["systemctl", "service"]:
            action = args[0] if args else ""
            service_name = args[1] if len(args) > 1 else ""
            if cmd == "service":
                service_name = args[0] if args else ""
                action = args[1] if len(args) > 1 else ""
            
            if "status" in action or "status" in args:
                return make_prompt(
                    f"● {service_name}.service - High performance web server\r\n"
                    f"   Loaded: loaded (/lib/systemd/system/{service_name}.service; enabled; vendor preset: enabled)\r\n"
                    f"   Active: active (running) since Sat 2026-07-11 09:03:55 UTC; 10min ago\r\n"
                    f" Main PID: 812 ({service_name})\r\n"
                    f"    Tasks: 2 (limit: 1153)\r\n"
                    f"   Memory: 8.2M\r\n"
                    f"   CGroup: /system.slice/{service_name}.service"
                )
            elif "restart" in action or "start" in action or "stop" in action:
                return make_prompt()
            return make_prompt("Usage: systemctl [start|stop|restart|status] service")
        elif cmd in ["useradd", "chown", "chgrp", "kill"]:
            return make_prompt()
        elif cmd == "sleep":
            if "&" in args or (len(args) > 1 and args[1] == "&"):
                return make_prompt("[1] 10485")
            return make_prompt()
        elif cmd == "jobs":
            return make_prompt("[1]+  Running                 bash capstone/src/app.sh > capstone/app.log &")
        elif cmd == "fg":
            return make_prompt("bash capstone/src/app.sh > capstone/app.log")
        elif cmd == "umask":
            return make_prompt("0022")
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
        elif cmd == "for":
            try:
                cmd_lower = cmd_line.lower()
                in_idx = cmd_lower.find(" in ")
                semi_idx = cmd_lower.find(";")
                do_idx = cmd_lower.find(" do ")
                done_idx = cmd_lower.rfind("done")
                if in_idx != -1 and semi_idx != -1 and do_idx != -1:
                    var_name = cmd_line[4:in_idx].strip()
                    items_str = cmd_line[in_idx+4:semi_idx].strip()
                    items = items_str.split()
                    echo_cmd_part = cmd_line[do_idx+4:done_idx].strip().strip(";").strip()
                    output_lines = []
                    for item in items:
                        curr_cmd = echo_cmd_part.replace(f"${var_name}", item)
                        res = self.execute_command(curr_cmd)
                        prompt_marker = "student@devlab:~"
                        if prompt_marker in res:
                            res = res.split(prompt_marker)[0].strip()
                        if res:
                            output_lines.append(res)
                    return make_prompt("\r\n".join(output_lines))
            except Exception as e:
                logger.error(f"Failed to parse simulated for loop: {e}")
                return make_prompt("bash: syntax error near unexpected token 'for'")
            return make_prompt("bash: syntax error near unexpected token 'for'")
        elif cmd == "if":
            try:
                cmd_lower = cmd_line.lower()
                then_idx = cmd_lower.find("; then ")
                else_idx = cmd_lower.find("; else ")
                fi_idx = cmd_lower.rfind("; fi")
                if fi_idx == -1:
                    fi_idx = cmd_lower.rfind(" fi")
                if then_idx != -1:
                    condition = cmd_line[3:then_idx].strip().strip("[").strip("]").strip()
                    parts_cond = condition.split()
                    is_true = False
                    if len(parts_cond) >= 2:
                        test_flag = parts_cond[0]
                        test_path = parts_cond[1]
                        local_test_path = self.get_local_path(test_path)
                        if test_flag == "-f":
                            is_true = os.path.exists(local_test_path) and os.path.isfile(local_test_path)
                        elif test_flag == "-d":
                            is_true = os.path.exists(local_test_path) and os.path.isdir(local_test_path)
                        elif test_flag == "-e":
                            is_true = os.path.exists(local_test_path)
                    then_branch = ""
                    else_branch = ""
                    if else_idx != -1:
                        then_branch = cmd_line[then_idx+7:else_idx].strip()
                        else_branch = cmd_line[else_idx+7:fi_idx].strip()
                    else:
                        then_branch = cmd_line[then_idx+7:fi_idx].strip()
                    target_branch = then_branch if is_true else else_branch
                    if target_branch:
                        res = self.execute_command(target_branch)
                        prompt_marker = "student@devlab:~"
                        if prompt_marker in res:
                            res = res.split(prompt_marker)[0].strip()
                        return make_prompt(res)
                    else:
                        return make_prompt()
            except Exception as e:
                logger.error(f"Failed to parse simulated if conditional: {e}")
                return make_prompt("bash: syntax error near unexpected token 'if'")
            return make_prompt("bash: syntax error near unexpected token 'if'")
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
        self.mock_networks = ["bridge", "host", "none"]
        self.mock_images = ["alpine", "hello-world", "nginx", "redis"]
        self.mock_compose_active = False

    def execute_command(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""

        # Normalize docker-compose script execution to docker compose
        if cmd_line.startswith("docker-compose"):
            cmd_line = cmd_line.replace("docker-compose", "docker compose", 1)

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
            
            if sub == "--version" or sub == "-v" or sub == "version":
                return make_prompt("Docker version 24.0.7, build afdd53b")
            elif sub == "info":
                return make_prompt(
                    f"Kernel Version: 6.8.0-1002-aws\r\n"
                    f"Operating System: Ubuntu 24.04 LTS\r\n"
                    f"Containers: {len(self.mock_containers)}\r\n"
                    f"Images: {len(self.mock_images)}"
                )
            elif sub == "run":
                name = "mock_container_" + secrets.token_hex(4)
                env_dict = {}
                volumes_list = []
                network_val = "bridge"
                ports_list = []
                
                run_args = args[1:]
                i = 0
                image = None
                cmd_args = []
                while i < len(run_args):
                    a = run_args[i]
                    if a == "--name" and i + 1 < len(run_args):
                        name = run_args[i+1]
                        i += 2
                    elif (a == "-e" or a == "--env") and i + 1 < len(run_args):
                        eq_part = run_args[i+1].split("=")
                        if len(eq_part) == 2:
                            env_dict[eq_part[0]] = eq_part[1].strip('"\'')
                        i += 2
                    elif (a == "-v" or a == "--volume") and i + 1 < len(run_args):
                        volumes_list.append(run_args[i+1])
                        i += 2
                    elif a == "--network" and i + 1 < len(run_args):
                        network_val = run_args[i+1]
                        i += 2
                    elif (a == "-p" or a == "--publish") and i + 1 < len(run_args):
                        ports_list.append(run_args[i+1])
                        i += 2
                    elif a.startswith("-"):
                        i += 1
                    else:
                        image = a
                        cmd_args = run_args[i+1:]
                        break

                if not image:
                    return make_prompt("docker run requires at least an image name.")

                c_id = secrets.token_hex(16)
                self.mock_containers[name] = {
                    "id": c_id,
                    "image": image,
                    "status": "exited" if "hello-world" in image else "running",
                    "env": env_dict,
                    "network": network_val,
                    "volumes": volumes_list,
                    "ports": ports_list
                }
                if "hello-world" in image:
                    return make_prompt(
                        "Hello from Docker!\r\n"
                        "This message shows that your installation appears to be working correctly.\r\n"
                        "To generate this message, Docker took the following steps:\r\n"
                        " 1. The Docker client contacted the Docker daemon.\r\n"
                        " 2. The Docker daemon pulled the \"hello-world\" image from the Docker Hub."
                    )
                return make_prompt(c_id)
            elif sub == "ps" or (sub == "container" and len(args) > 1 and args[1] == "ls"):
                show_all = "-a" in args or (len(args) > 2 and args[2] == "-a")
                lines = ["CONTAINER ID   IMAGE         COMMAND                  CREATED         STATUS         PORTS     NAMES"]
                for c_name, c_info in self.mock_containers.items():
                    if show_all or c_info["status"] == "running":
                        ports_str = " ".join(c_info["ports"]) if c_info["ports"] else "80/tcp"
                        status_str = "Up 10 seconds" if c_info["status"] == "running" else "Exited (0) Just now"
                        lines.append(f"{c_info['id'][:12]}   {c_info['image'][:12]:<12} \"/entrypoint.sh\"        10 seconds ago  {status_str:<15} {ports_str:<9} {c_name}")
                return make_prompt("\r\n".join(lines))
            elif sub == "images" or (sub == "image" and len(args) > 1 and args[1] == "ls"):
                lines = ["REPOSITORY      TAG       IMAGE ID       CREATED        SIZE"]
                for img in self.mock_images:
                    tag = "latest"
                    repo = img
                    if ":" in img:
                        repo, tag = img.split(":", 1)
                    img_id = secrets.token_hex(6)
                    lines.append(f"{repo:<16}{tag:<10}{img_id:<15}2 hours ago    12.1MB")
                return make_prompt("\r\n".join(lines))
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
            elif sub == "build":
                local_df = self.get_local_path(os.path.join(self.cwd, "Dockerfile"))
                local_df_multi = self.get_local_path(os.path.join(self.cwd, "Dockerfile.multi"))
                
                # Check for -f custom dockerfile
                df_to_use = local_df
                if "-f" in args:
                    f_idx = args.index("-f")
                    if f_idx + 1 < len(args):
                        df_to_use = self.get_local_path(os.path.join(self.cwd, args[f_idx+1]))

                if not os.path.exists(df_to_use):
                    return make_prompt(
                        "Error: failed to solve: failed to read dockerfile: "
                        "open Dockerfile: no such file or directory"
                    )

                tag = "unnamed_image:latest"
                if "-t" in args:
                    idx = args.index("-t")
                    if idx + 1 < len(args):
                        tag = args[idx + 1]

                try:
                    with open(df_to_use, "r", encoding="utf-8", errors="ignore") as f:
                        df_lines = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
                except Exception:
                    df_lines = ["FROM alpine"]

                is_cached = tag in self.mock_images
                if not is_cached:
                    self.mock_images.append(tag)

                build_steps = ["Sending build context to Docker daemon  2.048kB"]
                for i, step in enumerate(df_lines, start=1):
                    build_steps.append(f"Step {i}/{len(df_lines)} : {step}")
                    if is_cached:
                        build_steps.append(" ---> Using cache")
                    else:
                        build_steps.append(" ---> Running in intermediate container")
                build_steps.append("Successfully built 1f2113ea1a0c")
                build_steps.append(f"Successfully tagged {tag}")
                return make_prompt("\r\n".join(build_steps))
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
                elif len(args) > 1 and args[1] == "rm":
                    v_name = args[2] if len(args) > 2 else ""
                    if v_name in self.mock_volumes:
                        self.mock_volumes.remove(v_name)
                    return make_prompt(v_name)
                return make_prompt("Usage: docker volume COMMAND")
            elif sub == "network":
                if len(args) > 1 and args[1] == "create":
                    n_name = args[2] if len(args) > 2 else "net1"
                    self.mock_networks.append(n_name)
                    return make_prompt(n_name)
                elif len(args) > 1 and args[1] == "ls":
                    lines = ["NETWORK ID     NAME          DRIVER         SCOPE"]
                    for n in self.mock_networks:
                        lines.append(f"a1b2c3d4e5f6   {n:<13} bridge         local")
                    return make_prompt("\r\n".join(lines))
                elif len(args) > 1 and args[1] == "rm":
                    n_name = args[2] if len(args) > 2 else ""
                    if n_name in self.mock_networks:
                        self.mock_networks.remove(n_name)
                    return make_prompt(n_name)
                return make_prompt("Usage: docker network COMMAND")
            elif sub == "logs":
                c_name = args[1] if len(args) > 1 else ""
                if c_name in self.mock_containers:
                    return make_prompt("Starting process logs stream...\r\nReady for HTTP requests on port 80.")
                return make_prompt(f"Error: No such container: {c_name}")
            elif sub == "exec":
                c_name = args[1] if len(args) > 1 else ""
                exec_cmd = " ".join(args[2:])
                if c_name in self.mock_containers:
                    if "date" in exec_cmd:
                        return make_prompt(datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y"))
                    elif "ping" in exec_cmd:
                        target = args[-1]
                        c_net = self.mock_containers[c_name]["network"]
                        target_container = self.mock_containers.get(target)
                        if target_container and target_container["network"] == c_net:
                            return make_prompt(
                                f"PING {target} (172.18.0.3) 56(84) bytes of data.\r\n"
                                f"64 bytes from {target} (172.18.0.3): icmp_seq=1 ttl=64 time=0.045 ms\r\n"
                                f"--- {target} ping statistics ---\r\n"
                                f"3 packets transmitted, 3 received, 0% packet loss"
                            )
                        return make_prompt("ping: unknown host " + target)
                    return make_prompt("exec command completed.")
                return make_prompt(f"Error: No such container: {c_name}")
            elif sub == "inspect" or (sub == "image" and len(args) > 1 and args[1] == "inspect"):
                resource = args[1] if len(args) > 1 else ""
                if sub == "image":
                    resource = args[2] if len(args) > 2 else ""
                
                mock_id = secrets.token_hex(16)
                mock_status = "running"
                mock_env = []
                mock_mounts = []
                mock_net = "bridge"

                if resource in self.mock_containers:
                    c = self.mock_containers[resource]
                    mock_id = c["id"]
                    mock_status = c["status"]
                    mock_env = [f"{k}={v}" for k, v in c["env"].items()]
                    mock_net = c["network"]
                    mock_mounts = [
                        {
                            "Type": "volume",
                            "Name": v.split(":")[0],
                            "Destination": v.split(":")[1],
                            "Driver": "local"
                        } for v in c["volumes"] if ":" in v
                    ]
                
                return make_prompt(
                    f'[\n'
                    f'  {{\n'
                    f'    "Id": "{mock_id}",\n'
                    f'    "Name": "/{resource}",\n'
                    f'    "State": {{"Status": "{mock_status}", "Running": {str(mock_status == "running").lower()}}},\n'
                    f'    "NetworkSettings": {{"Networks": {{"{mock_net}": {{"IPAddress": "172.18.0.3"}}}}}},\n'
                    f'    "Mounts": {json.dumps(mock_mounts)},\n'
                    f'    "Config": {{"Env": {json.dumps(mock_env)}}}\n'
                    f'  }}\n'
                    f']'
                )
            elif sub == "stop":
                c_name = args[1] if len(args) > 1 else ""
                if c_name in self.mock_containers:
                    self.mock_containers[c_name]["status"] = "exited"
                    return make_prompt(c_name)
                return make_prompt(f"Error: No such container: {c_name}")
            elif sub == "restart":
                c_name = args[1] if len(args) > 1 else ""
                if c_name in self.mock_containers:
                    self.mock_containers[c_name]["status"] = "running"
                    return make_prompt(c_name)
                return make_prompt(f"Error: No such container: {c_name}")
            elif sub == "rm" or (sub == "container" and len(args) > 1 and args[1] == "rm"):
                c_name = args[-1]
                if c_name in self.mock_containers:
                    self.mock_containers.pop(c_name)
                return make_prompt(c_name)
            elif sub == "rmi" or (sub == "image" and len(args) > 1 and args[1] == "rm"):
                img_name = args[-1]
                if img_name in self.mock_images:
                    self.mock_images.remove(img_name)
                return make_prompt(img_name)
            elif sub == "system":
                action = args[1] if len(args) > 1 else ""
                if action == "prune":
                    to_remove = [k for k, v in self.mock_containers.items() if v.get("status") == "exited"]
                    for k in to_remove:
                        self.mock_containers.pop(k)
                    return make_prompt("Deleted Containers: " + str(len(to_remove)) + "\r\nTotal reclaimed space: 142MB")
                return make_prompt(f"docker system: '{action}' is not a docker system command.")
            elif sub == "tag":
                if len(args) >= 3:
                    src, target = args[1], args[2]
                    if src in self.mock_images and target not in self.mock_images:
                        self.mock_images.append(target)
                return make_prompt()
            elif sub == "stats":
                lines = [
                    "CONTAINER ID   NAME             CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O         PIDS",
                ]
                for c_name, c_info in self.mock_containers.items():
                    if c_info["status"] == "running":
                        lines.append(f"{c_info['id'][:12]}   {c_name:<16} 0.15%     4.23MiB / 512MiB      0.82%     1.02kB / 2.31kB   0B / 0B           2")
                return make_prompt("\r\n".join(lines))
            elif sub == "top":
                c_name = args[1] if len(args) > 1 else ""
                if c_name in self.mock_containers and self.mock_containers[c_name]["status"] == "running":
                    return make_prompt("UID        PID  PPID  C STIME TTY          TIME CMD\r\nroot         1     0  0 09:15 ?        00:00:00 nginx: master process")
                return make_prompt(f"Error: No such container: {c_name}")
            elif sub == "save":
                return make_prompt("Saving image layers archive... done")
            elif sub == "load":
                return make_prompt("Loaded image: custom_app:latest")
            elif sub == "export":
                return make_prompt("Exporting container filesystem... done")
            elif sub == "import":
                return make_prompt("sha256:" + secrets.token_hex(32))
            elif sub == "compose":
                compose_action = args[1] if len(args) > 1 else ""
                if compose_action == "config":
                    local_compose = self.get_local_path(os.path.join(self.cwd, "docker-compose.yml"))
                    if not os.path.exists(local_compose):
                        return make_prompt("Error: docker-compose.yml file not found.")
                    try:
                        with open(local_compose, "r") as f:
                            return make_prompt(f.read())
                    except:
                        return make_prompt("Error reading docker-compose.yml")
                elif compose_action == "up":
                    local_compose = self.get_local_path(os.path.join(self.cwd, "docker-compose.yml"))
                    if not os.path.exists(local_compose):
                        return make_prompt("Error: docker-compose.yml file not found.")
                    
                    self.mock_compose_active = True
                    self.mock_containers["student_web_1"] = {
                        "id": secrets.token_hex(16), "image": "nginx", "status": "running",
                        "env": {}, "network": "student_default", "volumes": [], "ports": ["80:80"]
                    }
                    self.mock_containers["student_db_1"] = {
                        "id": secrets.token_hex(16), "image": "redis", "status": "running",
                        "env": {}, "network": "student_default", "volumes": [], "ports": ["6379"]
                    }
                    if "student_default" not in self.mock_networks:
                        self.mock_networks.append("student_default")
                    return make_prompt("Creating network \"student_default\" with the default driver\r\nCreating student_web_1 ... done\r\nCreating student_db_1  ... done")
                elif compose_action == "down":
                    self.mock_compose_active = False
                    self.mock_containers.pop("student_web_1", None)
                    self.mock_containers.pop("student_db_1", None)
                    return make_prompt("Stopping student_web_1 ... done\r\nStopping student_db_1 ... done\r\nRemoving network student_default ... done")
                elif compose_action == "ps":
                    lines = ["   Name                 Command               State     Ports"]
                    if self.mock_compose_active:
                        lines.append("student_db_1    docker-entrypoint.sh redis...   Up      6379/tcp")
                        lines.append("student_web_1   /docker-entrypoint.sh ngin...   Up      0.0.0.0:80->80/tcp")
                    return make_prompt("\r\n".join(lines))
                elif compose_action == "images":
                    lines = ["Container      Repository    Tag       Image Id       Size"]
                    if self.mock_compose_active:
                        lines.append("student_db_1   redis         latest    39005c77e62d   113MB")
                        lines.append("student_web_1  nginx         latest    605c77e624dd   142MB")
                    return make_prompt("\r\n".join(lines))
                elif compose_action == "logs":
                    return make_prompt("student_db_1  | Redis server starting...\r\nstudent_web_1 | Ready for HTTP requests on port 80.")
                elif compose_action == "exec":
                    service = args[2] if len(args) > 2 else ""
                    exec_cmd = args[3] if len(args) > 3 else ""
                    if service == "db" and "ping" in exec_cmd:
                        return make_prompt("PONG")
                    return make_prompt("exec command completed.")
                elif compose_action == "pull":
                    return make_prompt("Pulling web ... done\r\nPulling db ... done")
                elif compose_action == "build":
                    return make_prompt("Building services... done")
                elif compose_action == "restart":
                    return make_prompt("Restarting compose stack services... done")
                return make_prompt(f"docker compose: '{compose_action}' is not a compose command.")
            else:
                return make_prompt(f"docker: '{sub}' is not a docker command.\r\nSee 'docker --help' for a list of available commands.")

        return super().execute_command(cmd_line)


class SimulatedKubernetesShell(SimulatedShell):
    """
    Subclass of SimulatedShell that emulates Kubernetes kubectl and helm command line operations.
    """
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.mock_pods = {}
        self.mock_deployments = {}
        self.mock_services = {}
        self.mock_configmaps = {}
        self.mock_secrets = {}
        self.mock_namespaces = ["default", "kube-system", "kube-public"]
        self.mock_pvs = {}
        self.mock_pvcs = {}
        self.mock_ingresses = {}
        self.mock_hpas = {}
        self.mock_helm_charts = {}

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

        if cmd == "kubectl":
            if not args:
                return make_prompt("kubectl controls the Kubernetes cluster manager.\n\nUsage: kubectl [command] [TYPE] [NAME]")
            sub = args[0]

            if sub == "version":
                return make_prompt("Client Version: v1.30.0\nKustomize Version: v5.0.4-0.20230601165947-6ce0ee390c3a")
            
            elif sub == "get":
                if len(args) < 2:
                    return make_prompt("error: You must specify the type of resource to get.")
                resource_type = args[1].lower()
                
                # Check for -n namespace flags
                target_ns = "default"
                if "-n" in args:
                    ns_idx = args.index("-n")
                    if ns_idx + 1 < len(args):
                        target_ns = args[ns_idx + 1]
                elif "--namespace" in args:
                    ns_idx = args.index("--namespace")
                    if ns_idx + 1 < len(args):
                        target_ns = args[ns_idx + 1]
                
                if resource_type in ["pod", "pods"]:
                    if not self.mock_pods:
                        return make_prompt("No resources found in default namespace.")
                    lines = ["NAME             READY   STATUS    RESTARTS   AGE"]
                    for name, p in self.mock_pods.items():
                        lines.append(f"{name:<16} 1/1     {p['status']:<9} 0          10s")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["deployment", "deployments", "deploy"]:
                    if not self.mock_deployments:
                        return make_prompt("No resources found in default namespace.")
                    lines = ["NAME              READY   UP-TO-DATE   AVAILABLE   AGE"]
                    for name, d in self.mock_deployments.items():
                        lines.append(f"{name:<17} {d['replicas']}/{d['replicas']}   {d['replicas']:<12} {d['replicas']:<11} 10s")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["service", "services", "svc"]:
                    lines = ["NAME             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE"]
                    lines.append("kubernetes       ClusterIP   10.43.0.1       <none>        443/TCP   1d")
                    for name, s in self.mock_services.items():
                        lines.append(f"{name:<16} {s['type']:<11} 10.43.50.99    <none>        {s['port']}/TCP  10s")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["namespace", "namespaces", "ns"]:
                    lines = ["NAME              STATUS   AGE"]
                    for ns in self.mock_namespaces:
                        lines.append(f"{ns:<17} Active   1d")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["replicaset", "replicasets", "rs"]:
                    if not self.mock_deployments:
                        return make_prompt("No resources found in default namespace.")
                    lines = ["NAME                        DESIRED   CURRENT   READY   AGE"]
                    for name, d in self.mock_deployments.items():
                        lines.append(f"{name}-a1b2c3d4e5   {d['replicas']:<9} {d['replicas']:<9} {d['replicas']:<7} 10s")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["configmap", "configmaps", "cm"]:
                    lines = ["NAME             DATA   AGE"]
                    for name, cm in self.mock_configmaps.items():
                        lines.append(f"{name:<16} {len(cm['data'])}      10s")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["secret", "secrets"]:
                    lines = ["NAME             TYPE     DATA   AGE"]
                    for name, sec in self.mock_secrets.items():
                        lines.append(f"{name:<16} Opaque   {len(sec['data'])}      10s")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["persistentvolume", "persistentvolumes", "pv"]:
                    lines = ["NAME             CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM   STORAGECLASS   REASON   AGE"]
                    for name, pv in self.mock_pvs.items():
                        lines.append(f"{name:<16} 5Gi        RWO            Retain           Bound    default/pvc    local-path              10s")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["persistentvolumeclaim", "persistentvolumeclaims", "pvc"]:
                    lines = ["NAME             STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE"]
                    for name, pvc in self.mock_pvcs.items():
                        lines.append(f"{name:<16} Bound    pv-local 5Gi        RWO            local-path     10s")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["ingress", "ingresses", "ing"]:
                    lines = ["NAME             CLASS    HOSTS          ADDRESS         PORTS   AGE"]
                    for name, ing in self.mock_ingresses.items():
                        lines.append(f"{name:<16} nginx    webapp.local   192.168.1.100   80      10s")
                    return make_prompt("\r\n".join(lines))
                    
                elif resource_type in ["horizontalpodautoscaler", "horizontalpodautoscalers", "hpa"]:
                    lines = ["NAME             REFERENCE               TARGETS         MINPODS   MAXPODS   REPLICAS   AGE"]
                    for name, hpa in self.mock_hpas.items():
                        lines.append(f"{name:<16} Deployment/webapp      0%/80%          1         10        3          10s")
                    return make_prompt("\r\n".join(lines))

                elif resource_type in ["cronjob", "cronjobs"]:
                    lines = ["NAME             SCHEDULE    SUSPEND   ACTIVE   LAST SCHEDULE   AGE"]
                    return make_prompt("\r\n".join(lines))

                elif resource_type in ["job", "jobs"]:
                    lines = ["NAME             COMPLETIONS   DURATION   AGE"]
                    return make_prompt("\r\n".join(lines))

                return make_prompt(f"error: the server doesn't have a resource type '{resource_type}'")

            elif sub == "create":
                if len(args) < 2:
                    return make_prompt("error: specify resource type to create.")
                c_type = args[1].lower()
                if c_type == "namespace":
                    name = args[2] if len(args) > 2 else ""
                    if name:
                        self.mock_namespaces.append(name)
                        return make_prompt(f"namespace/{name} created")
                    return make_prompt("error: namespace name not provided")
                elif c_type == "deployment":
                    name = args[2] if len(args) > 2 else ""
                    image = "nginx"
                    replicas = 1
                    for arg in args:
                        if arg.startswith("--image="):
                            image = arg.split("=")[1]
                        if arg.startswith("--replicas="):
                            try:
                                replicas = int(arg.split("=")[1])
                            except:
                                pass
                    if name:
                        self.mock_deployments[name] = {"image": image, "replicas": replicas}
                        for r in range(replicas):
                            p_name = f"{name}-{secrets.token_hex(4)}"
                            self.mock_pods[p_name] = {"image": image, "status": "Running"}
                        return make_prompt(f"deployment.apps/{name} created")
                    return make_prompt("error: deployment name not provided")
                elif c_type == "configmap":
                    name = args[2] if len(args) > 2 else ""
                    data = {}
                    for arg in args:
                        if arg.startswith("--from-literal="):
                            lit = arg.split("=")[1:]
                            lit_str = "=".join(lit)
                            if ":" in lit_str:
                                k, v = lit_str.split(":", 1)
                            elif "=" in lit_str:
                                k, v = lit_str.split("=", 1)
                            else:
                                k, v = "key", lit_str
                            data[k] = v
                    if name:
                        self.mock_configmaps[name] = {"data": data}
                        return make_prompt(f"configmap/{name} created")
                elif c_type == "secret":
                    sec_type = args[2] if len(args) > 2 else ""
                    name = args[3] if len(args) > 3 else ""
                    data = {}
                    for arg in args:
                        if arg.startswith("--from-literal="):
                            lit = arg.split("=")[1:]
                            lit_str = "=".join(lit)
                            if ":" in lit_str:
                                k, v = lit_str.split(":", 1)
                            elif "=" in lit_str:
                                k, v = lit_str.split("=", 1)
                            else:
                                k, v = "key", lit_str
                            data[k] = v
                    if name:
                        self.mock_secrets[name] = {"data": data}
                        return make_prompt(f"secret/{name} created")

                return make_prompt(f"error: cannot create resource type '{c_type}' via CLI shortcut. Please use YAML manifests.")

            elif sub == "expose":
                target_type = args[1].lower()
                name = args[2] if len(args) > 2 else ""
                port = 80
                name_svc = name
                for arg in args:
                    if arg.startswith("--port="):
                        port = arg.split("=")[1]
                    if arg.startswith("--name="):
                        name_svc = arg.split("=")[1]
                if target_type == "deployment" and name in self.mock_deployments:
                    self.mock_services[name_svc] = {"type": "ClusterIP", "port": port}
                    return make_prompt(f"service/{name_svc} exposed")
                return make_prompt(f"error: deployment '{name}' not found")

            elif sub == "scale":
                dep_name = ""
                for arg in args:
                    if arg.startswith("deployment/"):
                        dep_name = arg.split("/")[1]
                replicas = 1
                for arg in args:
                    if arg.startswith("--replicas="):
                        replicas = int(arg.split("=")[1])
                if dep_name in self.mock_deployments:
                    self.mock_deployments[dep_name]["replicas"] = replicas
                    self.mock_pods = {k: v for k, v in self.mock_pods.items() if not k.startswith(dep_name)}
                    for r in range(replicas):
                        p_name = f"{dep_name}-{secrets.token_hex(4)}"
                        self.mock_pods[p_name] = {"image": self.mock_deployments[dep_name]["image"], "status": "Running"}
                    return make_prompt(f"deployment.apps/{dep_name} scaled")
                return make_prompt(f"error: deployment '{dep_name}' not found")

            elif sub == "apply":
                f_path = ""
                for arg in args:
                    if arg == "-f" and args.index(arg) + 1 < len(args):
                        f_path = args[args.index(arg) + 1]
                local_file = self.get_local_path(f_path)
                if not os.path.exists(local_file):
                    return make_prompt(f"error: the path '{f_path}' does not exist")
                try:
                    with open(local_file, "r") as f:
                        content = f.read()
                    
                    kind = ""
                    name = ""
                    image = ""
                    replicas = 1
                    for line in content.splitlines():
                        line = line.strip()
                        if line.startswith("kind:"):
                            kind = line.split(":")[1].strip()
                        elif line.startswith("name:") and not name:
                            name = line.split(":")[1].strip()
                        elif line.startswith("image:"):
                            image = line.split(":")[1].strip()
                        elif line.startswith("replicas:"):
                            replicas = int(line.split(":")[1].strip())
                    
                    if kind == "Pod":
                        self.mock_pods[name] = {"image": image or "nginx", "status": "Running"}
                        return make_prompt(f"pod/{name} created")
                    elif kind == "Deployment":
                        self.mock_deployments[name] = {"image": image or "nginx", "replicas": replicas}
                        for r in range(replicas):
                            p_name = f"{name}-{secrets.token_hex(4)}"
                            self.mock_pods[p_name] = {"image": image or "nginx", "status": "Running"}
                        return make_prompt(f"deployment.apps/{name} created")
                    elif kind == "Service":
                        self.mock_services[name] = {"type": "ClusterIP", "port": 80}
                        return make_prompt(f"service/{name} created")
                    elif kind == "ConfigMap":
                        self.mock_configmaps[name] = {"data": {"APP_ENV": "prod"}}
                        return make_prompt(f"configmap/{name} created")
                    elif kind == "Secret":
                        self.mock_secrets[name] = {"data": {"password": "secretpassword"}}
                        return make_prompt(f"secret/{name} created")
                    elif kind == "PersistentVolume":
                        self.mock_pvs[name] = {}
                        return make_prompt(f"persistentvolume/{name} created")
                    elif kind == "PersistentVolumeClaim":
                        self.mock_pvcs[name] = {}
                        return make_prompt(f"persistentvolumeclaim/{name} created")
                    elif kind == "Ingress":
                        self.mock_ingresses[name] = {}
                        return make_prompt(f"ingress.networking.k8s.io/{name} created")
                    elif kind == "HorizontalPodAutoscaler":
                        self.mock_hpas[name] = {}
                        return make_prompt(f"horizontalpodautoscaler.autoscaling/{name} created")
                        
                    return make_prompt("manifest applied successfully.")
                except Exception as e:
                    return make_prompt(f"error: failed to parse YAML: {e}")

            elif sub == "delete":
                if len(args) < 3:
                    return make_prompt("error: specify resource type and name to delete.")
                res_type = args[1].lower()
                res_name = args[2]
                if res_type in ["pod", "pods"]:
                    self.mock_pods.pop(res_name, None)
                    return make_prompt(f"pod \"{res_name}\" deleted")
                elif res_type in ["deployment", "deployments", "deploy"]:
                    self.mock_deployments.pop(res_name, None)
                    self.mock_pods = {k: v for k, v in self.mock_pods.items() if not k.startswith(res_name)}
                    return make_prompt(f"deployment.apps \"{res_name}\" deleted")
                elif res_type in ["service", "services", "svc"]:
                    self.mock_services.pop(res_name, None)
                    return make_prompt(f"service \"{res_name}\" deleted")
                elif res_type in ["namespace", "namespaces", "ns"]:
                    if res_name in self.mock_namespaces:
                        self.mock_namespaces.remove(res_name)
                    return make_prompt(f"namespace \"{res_name}\" deleted")
                return make_prompt(f"resource \"{res_name}\" deleted")

            elif sub == "describe":
                if len(args) < 3:
                    return make_prompt("error: specify resource type and name to describe.")
                res_type = args[1].lower()
                res_name = args[2]
                return make_prompt(f"Name: {res_name}\nNamespace: default\nLabels: app={res_name}\nStatus: Running\nIP: 172.30.1.20")

            elif sub == "logs":
                pod_name = args[1] if len(args) > 1 else ""
                return make_prompt(f"Log stream from {pod_name}:\n[info] Application started successfully.\n[info] Listening on port 80.")

            elif sub == "exec":
                return make_prompt("exec command output verified.")

            elif sub == "rollout":
                action = args[1] if len(args) > 1 else ""
                target = args[2] if len(args) > 2 else ""
                return make_prompt(f"rollout {action} for {target} successfully completed")

            return make_prompt(f"kubectl: '{sub}' is not a kubectl subcommand.")

        elif cmd == "helm":
            if not args:
                return make_prompt("Helm is the package manager for Kubernetes.\n\nUsage: helm [command]")
            sub = args[0]
            if sub == "list" or sub == "ls":
                lines = ["NAME     NAMESPACE REVISION UPDATED                                  STATUS   CHART        APP VERSION"]
                for k, v in self.mock_helm_charts.items():
                    lines.append(f"{k:<8} default   1        2026-07-18 09:25:14.398000 +0530 DEPLOYED {v:<12} 1.0.0")
                return make_prompt("\r\n".join(lines))
            elif sub == "install":
                release_name = args[1] if len(args) > 1 else "my-release"
                chart_name = args[2] if len(args) > 2 else "nginx-chart"
                self.mock_helm_charts[release_name] = chart_name
                return make_prompt(f"NAME: {release_name}\nLAST DEPLOYED: Sat Jul 18 09:25:14 2026\nNAMESPACE: default\nSTATUS: deployed\nREVISION: 1")
            return make_prompt(f"helm: '{sub}' is not a helm subcommand.")

        return super().execute_command(cmd_line)


class GitShell(SimulatedShell):
    """
    A real host-based subshell that executes git and basic CLI utilities
    inside the session's Git repository.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"git-{session_id}")
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.cwd = "/"
        self.history = []

    def get_local_path(self, virtual_path: str) -> str:
        clean_vpath = virtual_path.strip().lstrip("/")
        if not clean_vpath:
            return self.base_dir
        return os.path.abspath(os.path.join(self.base_dir, clean_vpath))

    def execute_command(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""

        self.history.append(cmd_line)
        parts = cmd_line.split()
        cmd = parts[0]
        
        def make_prompt(output_text: str = "") -> str:
            suffix = "\r\n" if output_text and not output_text.endswith("\r\n") else ""
            return f"{output_text}{suffix}student@devlab-git:$ "

        # Whitelist safe commands
        if cmd not in ["git", "ls", "cat", "echo", "touch", "mkdir", "rm", "pwd", "clear"]:
            return make_prompt(f"bash: {cmd}: command not allowed in Git labs.")

        if cmd == "pwd":
            return make_prompt("/")

        # Run command using subprocess inside session directory
        try:
            res = subprocess.run(
                cmd_line,
                cwd=self.base_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            output = res.stdout
            if res.stderr:
                output += "\n" + res.stderr
            output_formatted = output.replace("\r\n", "\n").replace("\n", "\r\n")
            return make_prompt(output_formatted)
        except subprocess.TimeoutExpired:
            return make_prompt("Error: Command execution timed out.")
        except Exception as e:
            return make_prompt(f"Error: Command failed: {e}")


class GitHubActionsShell(GitShell):
    """
    A real host-based subshell that executes git and basic CLI utilities
    inside the session's Git repository, with simulated GitHub Actions workflow trigger on push.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"actions-{session_id}")
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.cwd = "/"
        self.history = []
        self.workflow_executed = False

    def execute_command(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""

        self.history.append(cmd_line)
        parts = cmd_line.split()
        cmd = parts[0]
        
        def make_prompt(output_text: str = "") -> str:
            suffix = "\r\n" if output_text and not output_text.endswith("\r\n") else ""
            return f"{output_text}{suffix}student@devlab-actions:$ "

        # Whitelist safe commands
        if cmd not in ["git", "ls", "cat", "echo", "touch", "mkdir", "rm", "pwd", "clear"]:
            return make_prompt(f"bash: {cmd}: command not allowed in GitHub Actions labs.")

        if cmd == "pwd":
            return make_prompt("/")

        # Run command using subprocess inside session directory
        try:
            res = subprocess.run(
                cmd_line,
                cwd=self.base_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            output = res.stdout
            if res.stderr:
                output += "\n" + res.stderr
            output_formatted = output.replace("\r\n", "\n").replace("\n", "\r\n")

            # Check if command was a git push
            if cmd == "git" and len(parts) > 1 and parts[1] == "push":
                workflow_path = os.path.join(self.base_dir, ".github/workflows/main.yml")
                if os.path.exists(workflow_path):
                    try:
                        import yaml
                        with open(workflow_path, "r") as f:
                            yaml_data = yaml.safe_load(f) or {}
                        
                        job_name = "build-and-test"
                        if isinstance(yaml_data.get("jobs"), dict):
                            job_name = list(yaml_data["jobs"].keys())[0]

                        actions_log = (
                            "\r\n\r\n"
                            "[\x1b[32mGitHub Actions\x1b[0m] Triggered by push on branch main...\r\n"
                            "[\x1b[32mGitHub Actions\x1b[0m] Run ID: 87429188\r\n"
                            f"[\x1b[32mGitHub Actions\x1b[0m] Job: {job_name}\r\n"
                            "-------------------------------------------------\r\n"
                            "1. Set up job... \x1b[32mSuccess\x1b[0m\r\n"
                            "2. Checkout repository... \x1b[32mSuccess\x1b[0m\r\n"
                            "3. Install dependencies... \x1b[32mSuccess\x1b[0m\r\n"
                            "4. Run tests... \x1b[32mSuccess\x1b[0m\r\n"
                            "5. Build project... \x1b[32mSuccess\x1b[0m\r\n"
                            "6. Upload artifact... \x1b[32mSuccess\x1b[0m\r\n"
                            "-------------------------------------------------\r\n"
                            "[\x1b[32mGitHub Actions\x1b[0m] Workflow completed successfully!\r\n"
                        )
                        output_formatted += actions_log
                        self.workflow_executed = True
                    except Exception as ye:
                        output_formatted += f"\r\n\r\n[\x1b[31mGitHub Actions Parser Error\x1b[0m] Invalid YAML syntax: {ye}\r\n"
                else:
                    output_formatted += "\r\n\r\n[GitHub Actions] No workflows configured in .github/workflows/main.yml.\r\n"

            return make_prompt(output_formatted)
        except subprocess.TimeoutExpired:
            return make_prompt("Error: Command execution timed out.")
        except Exception as e:
            return make_prompt(f"Error: Command failed: {e}")


class CICDShell(GitShell):
    """
    A real host-based subshell that executes git, custom pipeline tools,
    and basic CLI utilities inside the session's repository.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"cicd-{session_id}")
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.cwd = "/"
        self.history = []
        self.pipeline_executed = False

    def execute_command(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""

        self.history.append(cmd_line)
        parts = cmd_line.split()
        cmd = parts[0]
        
        def make_prompt(output_text: str = "") -> str:
            suffix = "\r\n" if output_text and not output_text.endswith("\r\n") else ""
            return f"{output_text}{suffix}student@devlab-cicd:$ "

        # Whitelist safe commands (including run-pipeline)
        if cmd not in ["git", "ls", "cat", "echo", "touch", "mkdir", "rm", "pwd", "clear", "run-pipeline"]:
            return make_prompt(f"bash: {cmd}: command not allowed in CI/CD labs.")

        if cmd == "pwd":
            return make_prompt("/")

        if cmd == "run-pipeline":
            pipeline_path = os.path.join(self.base_dir, "pipeline.yml")
            if not os.path.exists(pipeline_path):
                return make_prompt("[Pipeline] Error: pipeline.yml config file not found.")
            
            try:
                import yaml
                with open(pipeline_path, "r") as f:
                    yaml_data = yaml.safe_load(f) or {}
                
                stages = yaml_data.get("stages", [])
                if not isinstance(stages, list) or not stages:
                    return make_prompt("[Pipeline] Error: No stages list configured in pipeline.yml.")
                
                log_lines = [
                    "[\x1b[34mPipeline\x1b[0m] Starting pipeline execution...",
                    "[\x1b[34mPipeline\x1b[0m] -------------------------------------------------"
                ]
                for idx, stage in enumerate(stages, 1):
                    log_lines.append(f"[\x1b[34mPipeline\x1b[0m] Stage {idx}: {stage} ... \x1b[32mSuccess\x1b[0m")
                log_lines.append("[\x1b[34mPipeline\x1b[0m] -------------------------------------------------")
                log_lines.append("[\x1b[34mPipeline\x1b[0m] Pipeline completed successfully!")
                
                self.pipeline_executed = True
                return make_prompt("\r\n".join(log_lines))
            except Exception as ye:
                return make_prompt(f"[Pipeline] YAML Parse Error: Invalid syntax: {ye}")

        # Run command using subprocess inside session directory
        try:
            res = subprocess.run(
                cmd_line,
                cwd=self.base_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            output = res.stdout
            if res.stderr:
                output += "\n" + res.stderr
            output_formatted = output.replace("\r\n", "\n").replace("\n", "\r\n")
            return make_prompt(output_formatted)
        except subprocess.TimeoutExpired:
            return make_prompt("Error: Command execution timed out.")
        except Exception as e:
            return make_prompt(f"Error: Command failed: {e}")


class JenkinsShell(GitShell):
    """
    A real host-based subshell that executes git, custom jenkins builds,
    and basic CLI utilities inside the session's repository.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"jenkins-{session_id}")
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.cwd = "/"
        self.history = []
        self.jenkins_executed = False

    def execute_command(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line:
            return ""

        self.history.append(cmd_line)
        parts = cmd_line.split()
        cmd = parts[0]
        
        def make_prompt(output_text: str = "") -> str:
            suffix = "\r\n" if output_text and not output_text.endswith("\r\n") else ""
            return f"{output_text}{suffix}student@devlab-jenkins:$ "

        # Whitelist safe commands (including jenkins)
        if cmd not in ["git", "ls", "cat", "echo", "touch", "mkdir", "rm", "pwd", "clear", "jenkins"]:
            return make_prompt(f"bash: {cmd}: command not allowed in Jenkins labs.")

        if cmd == "pwd":
            return make_prompt("/")

        if cmd == "jenkins":
            if len(parts) < 2 or parts[1] != "build":
                return make_prompt("Usage: jenkins build")
                
            jenkinsfile_path = os.path.join(self.base_dir, "Jenkinsfile")
            if not os.path.exists(jenkinsfile_path):
                return make_prompt("[Jenkins] Error: Jenkinsfile config file not found.")
            
            try:
                # Read Jenkinsfile text and extract stages
                with open(jenkinsfile_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Extract stage names using a simple regex/parser
                import re
                stage_names = re.findall(r'stage\s*\(\s*["\']([^"\']+)["\']\s*\)', content)
                
                log_lines = [
                    "[\x1b[35mJenkins\x1b[0m] Starting pipeline execution (Build #1)...",
                    "[\x1b[35mJenkins\x1b[0m] -------------------------------------------------"
                ]
                if not stage_names:
                    # Let's see if it's a scripted pipeline without standard quotes or standard stages
                    # If empty, default to checking checkout/build/test/deploy keywords
                    keywords = ["Checkout", "Build", "Test", "Deploy", "Install", "Freestyle", "Notify", "Archive"]
                    for kw in keywords:
                        if kw.lower() in content.lower():
                            stage_names.append(kw)
                
                if not stage_names:
                    stage_names = ["Build"]
                
                for idx, stage in enumerate(stage_names, 1):
                    log_lines.append(f"[\x1b[35mJenkins\x1b[0m] Stage: {stage} ... \x1b[32mSuccess\x1b[0m")
                log_lines.append("[\x1b[35mJenkins\x1b[0m] -------------------------------------------------")
                log_lines.append("[\x1b[35mJenkins\x1b[0m] Pipeline completed successfully! (Build #1)")
                
                self.jenkins_executed = True
                return make_prompt("\r\n".join(log_lines))
            except Exception as ye:
                return make_prompt(f"[Jenkins] Syntax Error: Invalid Jenkinsfile syntax: {ye}")

        # Run command using subprocess inside session directory
        try:
            res = subprocess.run(
                cmd_line,
                cwd=self.base_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            output = res.stdout
            if res.stderr:
                output += "\n" + res.stderr
            output_formatted = output.replace("\r\n", "\n").replace("\n", "\r\n")
            return make_prompt(output_formatted)
        except subprocess.TimeoutExpired:
            return make_prompt("Error: Command execution timed out.")
        except Exception as e:
            return make_prompt(f"Error: Command failed: {e}")


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

class KubernetesRuntime(BaseRuntime):
    """
    Kubernetes runtime provisioner managing secure namespace sandboxes,
    RBAC setup, and Sandbox Pod creation for live K3s setups.
    """
    def __init__(self):
        self.is_active = False
        if K8S_AVAILABLE:
            try:
                # Load configuration from KUBECONFIG_PATH setting
                if os.path.exists(settings.KUBECONFIG_PATH):
                    k8s_config.load_kube_config(config_file=settings.KUBECONFIG_PATH)
                else:
                    k8s_config.load_kube_config()
                # Run a fast ping check using API list
                k8s_client.CoreV1Api().list_node(limit=1)
                self.is_active = True
                logger.info("Successfully connected to K3s/Kubernetes cluster!")
            except Exception as e:
                logger.warning(f"Could not connect to K3s cluster: {e}. Fallback to simulated mode.")

    def create_session(self, session_id: str) -> Dict[str, Any]:
        if not self.is_active or not K8S_AVAILABLE:
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

        ns_name = f"devlab-ns-{session_id}"
        try:
            v1 = k8s_client.CoreV1Api()
            rbac = k8s_client.RbacAuthorizationV1Api()

            # 1. Provision isolated Namespace
            ns = k8s_client.V1Namespace(metadata=k8s_client.V1ObjectMeta(name=ns_name))
            v1.create_namespace(ns)

            # 2. Create ServiceAccount
            sa = k8s_client.V1ServiceAccount(metadata=k8s_client.V1ObjectMeta(name="devlab-sa"))
            v1.create_namespaced_service_account(ns_name, sa)

            # 3. Create Role (restricted permissions within the namespace)
            role = k8s_client.V1Role(
                metadata=k8s_client.V1ObjectMeta(name="devlab-role"),
                rules=[
                    k8s_client.V1PolicyRule(
                        api_groups=["", "apps", "batch", "autoscaling", "networking.k8s.io"],
                        resources=["*"],
                        verbs=["*"]
                    )
                ]
            )
            rbac.create_namespaced_role(ns_name, role)

            # 4. Create RoleBinding
            binding = k8s_client.V1RoleBinding(
                metadata=k8s_client.V1ObjectMeta(name="devlab-role-binding"),
                subjects=[
                    k8s_client.V1Subject(
                        kind="ServiceAccount",
                        name="devlab-sa",
                        namespace=ns_name
                    )
                ],
                role_ref=k8s_client.V1RoleRef(
                    kind="Role",
                    name="devlab-role",
                    api_group="rbac.authorization.k8s.io"
                )
            )
            rbac.create_namespaced_role_binding(ns_name, binding)

            # 5. Create Sandbox Pod with kubectl and helm
            sandbox_pod = k8s_client.V1Pod(
                metadata=k8s_client.V1ObjectMeta(name="devlab-sandbox", labels={"app": "devlab-sandbox"}),
                spec=k8s_client.V1PodSpec(
                    service_account_name="devlab-sa",
                    containers=[
                        k8s_client.V1Container(
                            name="sandbox",
                            image="ubuntu:24.04",
                            command=[
                                "/bin/sh", 
                                "-c", 
                                "apt-get update && apt-get install -y curl nano vim && "
                                "curl -LO https://dl.k8s.io/release/v1.30.0/bin/linux/amd64/kubectl && "
                                "chmod +x kubectl && mv kubectl /usr/local/bin/ && "
                                "curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && "
                                "chmod 700 get_helm.sh && ./get_helm.sh && "
                                "sleep 3600"
                            ]
                        )
                    ]
                )
            )
            v1.create_namespaced_pod(ns_name, sandbox_pod)

            return {"container_id": f"k8s-{session_id}", "status": "running", "mode": "k8s"}

        except Exception as e:
            logger.error(f"Failed to provision K8s resources for session {session_id}: {e}")
            self.stop_session(session_id)
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        if not self.is_active or not K8S_AVAILABLE:
            return

        ns_name = f"devlab-ns-{session_id}"
        v1 = k8s_client.CoreV1Api()
        try:
            v1.delete_namespace(ns_name, grace_period_seconds=0)
            logger.info(f"Successfully cleaned up namespace and RBAC structures: {ns_name}")
        except Exception as e:
            logger.warning(f"Error during namespace delete {ns_name}: {e}")


def _remove_readonly(func, path, excinfo):
    import stat
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


class GitRuntime(BaseRuntime):
    """
    Git runtime provisioner managing local session directory repositories.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"git-{session_id}")
        )
        os.makedirs(session_dir, exist_ok=True)
        
        try:
            # Run git init
            subprocess.run(["git", "init"], cwd=session_dir, capture_output=True, check=True)
            # Set git identity locally inside the repository config
            subprocess.run(["git", "config", "user.name", "DevLab Student"], cwd=session_dir, check=True)
            subprocess.run(["git", "config", "user.email", "student@devlab.io"], cwd=session_dir, check=True)
            
            # Create a simple welcome file
            with open(os.path.join(session_dir, "welcome.txt"), "w") as f:
                f.write("Welcome to DevLab Git Basics! Start by initializing or staging your work.\n")
                
            return {"container_id": f"git-{session_id}", "status": "running", "mode": "git"}
        except Exception as e:
            logger.error(f"GitRuntime failed to initialize repository: {e}")
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"git-{session_id}")
        )
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to remove Git session directory {session_dir}: {e}")


class GitHubActionsRuntime(BaseRuntime):
    """
    GitHub Actions runtime provisioner managing local session directories
    and local bare Git remote repositories.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"actions-{session_id}")
        )
        remote_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"actions-{session_id}-remote.git")
        )
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(remote_dir, exist_ok=True)
        
        try:
            # 1. Initialize bare remote repository
            subprocess.run(["git", "init", "--bare"], cwd=remote_dir, capture_output=True, check=True)
            
            # 2. Initialize student repository
            subprocess.run(["git", "init"], cwd=session_dir, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "DevLab Student"], cwd=session_dir, check=True)
            subprocess.run(["git", "config", "user.email", "student@devlab.io"], cwd=session_dir, check=True)
            
            # 3. Add remote origin pointing to the bare repository
            remote_path_slashes = remote_dir.replace("\\", "/")
            subprocess.run(["git", "remote", "add", "origin", remote_path_slashes], cwd=session_dir, check=True)
            
            # 4. Create a dummy initial commit so push is easy for the student
            with open(os.path.join(session_dir, "welcome.txt"), "w") as f:
                f.write("Welcome to DevLab GitHub Actions! Start by configuring your workflow YAML.\n")
            subprocess.run(["git", "add", "welcome.txt"], cwd=session_dir, check=True)
            subprocess.run(["git", "commit", "-m", "initial welcome commit"], cwd=session_dir, check=True)
            
            return {"container_id": f"actions-{session_id}", "status": "running", "mode": "actions"}
        except Exception as e:
            logger.error(f"GitHubActionsRuntime failed to initialize: {e}")
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"actions-{session_id}")
        )
        remote_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"actions-{session_id}-remote.git")
        )
        for path in [session_dir, remote_dir]:
            if os.path.exists(path):
                try:
                    shutil.rmtree(path, onerror=_remove_readonly)
                except Exception as e:
                    logger.warning(f"Failed to remove directory {path}: {e}")


class CICDRuntime(BaseRuntime):
    """
    CI/CD runtime provisioner managing local session directory repositories.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"cicd-{session_id}")
        )
        os.makedirs(session_dir, exist_ok=True)
        
        try:
            # 1. Initialize repository
            subprocess.run(["git", "init"], cwd=session_dir, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "DevLab Student"], cwd=session_dir, check=True)
            subprocess.run(["git", "config", "user.email", "student@devlab.io"], cwd=session_dir, check=True)
            
            # 2. Create welcome.txt
            with open(os.path.join(session_dir, "welcome.txt"), "w") as f:
                f.write("Welcome to DevLab CI/CD! Start by authoring your pipeline.yml configurations.\n")
            
            subprocess.run(["git", "add", "welcome.txt"], cwd=session_dir, check=True)
            subprocess.run(["git", "commit", "-m", "initial welcome commit"], cwd=session_dir, check=True)
            
            return {"container_id": f"cicd-{session_id}", "status": "running", "mode": "cicd"}
        except Exception as e:
            logger.error(f"CICDRuntime failed to initialize repository: {e}")
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"cicd-{session_id}")
        )
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to remove CI/CD session directory {session_dir}: {e}")


class JenkinsRuntime(BaseRuntime):
    """
    Jenkins runtime provisioner managing local session directory repositories.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"jenkins-{session_id}")
        )
        os.makedirs(session_dir, exist_ok=True)
        
        try:
            # 1. Initialize repository
            subprocess.run(["git", "init"], cwd=session_dir, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "DevLab Student"], cwd=session_dir, check=True)
            subprocess.run(["git", "config", "user.email", "student@devlab.io"], cwd=session_dir, check=True)
            
            # 2. Create welcome.txt
            with open(os.path.join(session_dir, "welcome.txt"), "w") as f:
                f.write("Welcome to DevLab Jenkins! Start by authoring your Jenkinsfile configuration.\n")
            
            subprocess.run(["git", "add", "welcome.txt"], cwd=session_dir, check=True)
            subprocess.run(["git", "commit", "-m", "initial welcome commit"], cwd=session_dir, check=True)
            
            return {"container_id": f"jenkins-{session_id}", "status": "running", "mode": "jenkins"}
        except Exception as e:
            logger.error(f"JenkinsRuntime failed to initialize repository: {e}")
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"jenkins-{session_id}")
        )
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to remove Jenkins session directory {session_dir}: {e}")


class TerraformShell(GitShell):
    """
    A real host-based subshell that executes basic CLI utilities and
    simulates Terraform commands inside the session's workspace.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"terraform-{session_id}")
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.cwd = "/"
        self.history = []
        self.tf_initialized = False
        self.tf_workspace = "default"
        self.tf_workspaces_list = ["default"]

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
            return f"{output_text}{suffix}student@devlab-terraform:$ "

        # Whitelist safe commands (including terraform)
        if cmd not in ["git", "ls", "cat", "echo", "touch", "mkdir", "rm", "pwd", "clear", "terraform"]:
            return make_prompt(f"bash: {cmd}: command not allowed in Terraform labs.")

        if cmd == "pwd":
            return make_prompt("/")

        if cmd == "terraform":
            if not args:
                return make_prompt("Usage: terraform <subcommand> [options]")
            sub = args[0]
            
            # Subcommand: init
            if sub == "init":
                # Find all .tf files in the directory
                tf_files = [f for f in os.listdir(self.base_dir) if f.endswith(".tf")]
                if not tf_files:
                    return make_prompt("Error: No Terraform configuration files (*.tf) found in the directory.")
                
                # Simulate downloading providers
                self.tf_initialized = True
                dot_tf_dir = os.path.join(self.base_dir, ".terraform")
                os.makedirs(dot_tf_dir, exist_ok=True)
                lock_file = os.path.join(self.base_dir, ".terraform.lock.hcl")
                with open(lock_file, "w") as lf:
                    lf.write('# Simulated lock file\nprovider "registry.terraform.io/hashicorp/local" {\n  version = "2.2.3"\n}\n')
                
                output = (
                    "\x1b[32mInitializing the backend...\x1b[0m\r\n"
                    "Initializing provider plugins...\r\n"
                    "- Finding hashicorp/local versions matching \"~> 2.0\"...\r\n"
                    "- Installing hashicorp/local v2.2.3...\r\n"
                    "- Installed hashicorp/local v2.2.3 (simulated)\r\n\r\n"
                    "\x1b[32mTerraform has been successfully initialized!\x1b[0m\r\n\r\n"
                    "You may now begin working with Terraform. Try running \"terraform plan\" to see\r\n"
                    "any changes that are required for your infrastructure."
                )
                return make_prompt(output)

            # Check if initialized for subcommands other than init/fmt/workspace
            if sub not in ["fmt", "workspace"] and not self.tf_initialized:
                return make_prompt("Error: Terraform not initialized. Please run 'terraform init' first.")

            # Subcommand: fmt
            if sub == "fmt":
                # Find all .tf files
                tf_files = [f for f in os.listdir(self.base_dir) if f.endswith(".tf")]
                formatted = []
                for tf in tf_files:
                    formatted.append(tf)
                output = "\r\n".join(formatted) if formatted else "No files formatted."
                return make_prompt(output)

            # Subcommand: validate
            if sub == "validate":
                tf_files = [f for f in os.listdir(self.base_dir) if f.endswith(".tf")]
                for tf in tf_files:
                    with open(os.path.join(self.base_dir, tf), "r", encoding="utf-8") as f:
                        content = f.read()
                        if content.count("{") != content.count("}"):
                            return make_prompt(f"\x1b[31mError:\x1b[0m Syntax error in {tf}: mismatched curly braces.")
                return make_prompt("\x1b[32mSuccess! The configuration is valid.\x1b[0m")

            # Subcommand: plan
            if sub == "plan":
                tf_files = [f for f in os.listdir(self.base_dir) if f.endswith(".tf")]
                import re
                resources = []
                for tf in tf_files:
                    with open(os.path.join(self.base_dir, tf), "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = re.findall(r'resource\s+["\']([^"\']+)["\']\s+["\']([^"\']+)["\']', content)
                        for r_type, r_name in matches:
                            resources.append(f"{r_type}.{r_name}")

                if not resources:
                    return make_prompt("No changes. Infrastructure is up-to-date.")

                plan_lines = [
                    "Terraform used the selected providers to generate the following execution plan.",
                    "Resource actions are indicated with the following symbols:",
                    "  \x1b[32m+\x1b[0m create",
                    "",
                    "Terraform will perform the following actions:",
                    ""
                ]
                for r in resources:
                    plan_lines.append(f"  \x1b[32m+ {r}\x1b[0m will be created")
                    plan_lines.append("      id:   (known after apply)")
                
                plan_lines.append("")
                plan_lines.append(f"\x1b[32mPlan:\x1b[0m {len(resources)} to add, 0 to change, 0 to destroy.")
                return make_prompt("\r\n".join(plan_lines))

            # Subcommand: apply
            if sub == "apply":
                tf_files = [f for f in os.listdir(self.base_dir) if f.endswith(".tf")]
                import re
                resources = []
                for tf in tf_files:
                    with open(os.path.join(self.base_dir, tf), "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = re.findall(r'resource\s+["\']([^"\']+)["\']\s+["\']([^"\']+)["\']', content)
                        for r_type, r_name in matches:
                            resources.append((r_type, r_name))

                if not resources:
                    return make_prompt("Apply complete! Resources: 0 added, 0 changed, 0 destroyed.")

                apply_lines = []
                for r_type, r_name in resources:
                    apply_lines.append(f"{r_type}.{r_name}: Creating...")
                    apply_lines.append(f"{r_type}.{r_name}: Creation complete after 1s [id={r_type}_{r_name}_id]")

                # Write terraform.tfstate file
                state_path = os.path.join(self.base_dir, "terraform.tfstate")
                state_data = {
                    "version": 4,
                    "terraform_version": "1.5.0",
                    "serial": 1,
                    "lineage": "simulated-lineage-uuid",
                    "outputs": {},
                    "resources": []
                }
                for r_type, r_name in resources:
                    state_data["resources"].append({
                        "mode": "managed",
                        "type": r_type,
                        "name": r_name,
                        "provider": "provider[\"registry.terraform.io/hashicorp/local\"]",
                        "instances": [
                            {
                                "schema_version": 0,
                                "attributes": {
                                    "id": f"{r_type}_{r_name}_id",
                                    "content": "Simulated content",
                                    "filename": "simulated.txt"
                                }
                            }
                        ]
                    })
                
                # Check for outputs and add to state
                for tf in tf_files:
                    with open(os.path.join(self.base_dir, tf), "r", encoding="utf-8") as f:
                        content = f.read()
                        out_matches = re.findall(r'output\s+["\']([^"\']+)["\']\s*\{', content)
                        for out_name in out_matches:
                            state_data["outputs"][out_name] = {
                                "type": "string",
                                "value": f"value_of_{out_name}"
                            }

                import json
                with open(state_path, "w", encoding="utf-8") as sf:
                    json.dump(state_data, sf, indent=2)

                apply_lines.append("")
                apply_lines.append(f"\x1b[32mApply complete! Resources: {len(resources)} added, 0 changed, 0 destroyed.\x1b[0m")
                return make_prompt("\r\n".join(apply_lines))

            # Subcommand: destroy
            if sub == "destroy":
                state_path = os.path.join(self.base_dir, "terraform.tfstate")
                if not os.path.exists(state_path):
                    return make_prompt("Error: No state file found. Nothing to destroy.")

                import json
                try:
                    with open(state_path, "r", encoding="utf-8") as sf:
                        state_data = json.load(sf)
                except Exception:
                    state_data = {"resources": []}

                destroy_lines = []
                for res in state_data.get("resources", []):
                    r_type = res["type"]
                    r_name = res["name"]
                    destroy_lines.append(f"{r_type}.{r_name}: Destroying...")
                    destroy_lines.append(f"{r_type}.{r_name}: Destruction complete after 1s")

                if os.path.exists(state_path):
                    os.remove(state_path)

                destroy_lines.append("")
                destroy_lines.append(f"\x1b[32mDestroy complete! Resources: {len(state_data.get('resources', []))} destroyed.\x1b[0m")
                return make_prompt("\r\n".join(destroy_lines))

            # Subcommand: output
            if sub == "output":
                state_path = os.path.join(self.base_dir, "terraform.tfstate")
                if not os.path.exists(state_path):
                    return make_prompt("Error: No outputs found or state file missing.")
                import json
                with open(state_path, "r", encoding="utf-8") as sf:
                    state_data = json.load(sf)
                outputs = state_data.get("outputs", {})
                if not outputs:
                    return make_prompt("No outputs defined.")
                out_lines = []
                for k, v in outputs.items():
                    out_lines.append(f"{k} = \"{v['value']}\"")
                return make_prompt("\r\n".join(out_lines))

            # Subcommand: state
            if sub == "state":
                if len(args) < 2 or args[1] != "list":
                    return make_prompt("Usage: terraform state list")
                state_path = os.path.join(self.base_dir, "terraform.tfstate")
                if not os.path.exists(state_path):
                    return make_prompt("No resources found in state.")
                import json
                with open(state_path, "r", encoding="utf-8") as sf:
                    state_data = json.load(sf)
                res_lines = []
                for r in state_data.get("resources", []):
                    res_lines.append(f"{r['type']}.{r['name']}")
                return make_prompt("\r\n".join(res_lines) if res_lines else "No resources in state.")

            # Subcommand: workspace
            if sub == "workspace":
                if len(args) < 2:
                    return make_prompt("Usage: terraform workspace [list/new/select]")
                w_action = args[1]
                if w_action == "list":
                    list_lines = []
                    for w in self.tf_workspaces_list:
                        prefix = "*" if w == self.tf_workspace else " "
                        list_lines.append(f"{prefix} {w}")
                    return make_prompt("\r\n".join(list_lines))
                elif w_action == "new":
                    if len(args) < 3:
                        return make_prompt("Error: workspace name required.")
                    w_name = args[2]
                    if w_name in self.tf_workspaces_list:
                        return make_prompt(f"Error: Workspace {w_name} already exists.")
                    self.tf_workspaces_list.append(w_name)
                    self.tf_workspace = w_name
                    w_dir = os.path.join(self.base_dir, "terraform.tfstate.d", w_name)
                    os.makedirs(w_dir, exist_ok=True)
                    return make_prompt(f"Created and switched to workspace \"{w_name}\"!")
                elif w_action == "select":
                    if len(args) < 3:
                        return make_prompt("Error: workspace name required.")
                    w_name = args[2]
                    if w_name not in self.tf_workspaces_list:
                        return make_prompt(f"Error: Workspace {w_name} does not exist.")
                    self.tf_workspace = w_name
                    return make_prompt(f"Switched to workspace \"{w_name}\"!")
                else:
                    return make_prompt(f"Error: workspace subcommand {w_action} not recognized.")

            return make_prompt(f"Error: terraform subcommand {sub} not recognized.")

        return super().execute_command(cmd_line)


class TerraformRuntime(BaseRuntime):
    """
    Terraform runtime provisioner managing local session workspace directories.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"terraform-{session_id}")
        )
        os.makedirs(session_dir, exist_ok=True)
        
        try:
            with open(os.path.join(session_dir, "main.tf"), "w") as f:
                f.write(
                    "# Welcome to Terraform on DevLab!\n"
                    "# Define your resources, variables, and providers configuration blocks here.\n"
                )
            
            return {"container_id": f"terraform-{session_id}", "status": "running", "mode": "terraform"}
        except Exception as e:
            logger.error(f"TerraformRuntime failed to initialize workspace: {e}")
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"terraform-{session_id}")
        )
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to remove Terraform session directory {session_dir}: {e}")


class MonitoringShell(GitShell):
    """
    A real host-based subshell that executes basic CLI utilities and
    simulates Prometheus, Grafana, Alertmanager, and Docker/K8s metrics commands.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"monitoring-{session_id}")
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.cwd = "/"
        self.history = []
        self.monitoring_state = {
            "configs": ["prometheus.yml", "alertmanager.yml"],
            "rules": ["rules.yml"],
            "silences": [],
            "dashboards": [],
            "datasources": ["Prometheus"],
            "alerts": []
        }

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
            return f"{output_text}{suffix}student@devlab-monitoring:$ "

        # Whitelist safe monitoring CLI tools
        monitoring_cmds = ["prometheus", "promtool", "amtool", "grafana-cli", "kubectl", "docker", "curl", "ssh"]
        if cmd not in ["git", "ls", "cat", "echo", "touch", "mkdir", "rm", "pwd", "clear"] + monitoring_cmds:
            return make_prompt(f"bash: {cmd}: command not allowed in Monitoring labs.")

        if cmd == "pwd":
            return make_prompt("/")

        if cmd == "promtool":
            if "check" in args and "config" in args:
                return make_prompt("Checking prometheus.yml  SUCCESS\n  12 targets validated, 0 errors found.")
            elif "check" in args and "rules" in args:
                return make_prompt("Checking rules.yml  SUCCESS\n  3 alert rules, 2 recording rules validated.")
            return make_prompt("promtool v2.45.0 (built with go1.20)")

        if cmd == "amtool":
            if "check-config" in args:
                return make_prompt("Checking alertmanager.yml  SUCCESS\n  1 route tree, 2 receiver targets validated.")
            elif "silence" in args:
                return make_prompt("ID                                   Matchers           Ends At                  Created By      Comment\n00000000-0000-0000-0000-000000000000  alertname=LowDisk  2026-12-31T23:59:59Z     student@devlab  Maintenance silence")
            return make_prompt("amtool v0.25.0 (Alertmanager CLI)")

        if cmd == "grafana-cli":
            return make_prompt("Grafana CLI v10.0.0\nInstalled plugins:\n - alexanderzobnin-zabbix-app\n - grafana-piechart-panel")

        if cmd == "kubectl":
            if "top" in args and "pods" in args:
                return make_prompt("NAME                            CPU(cores)   MEMORY(bytes)\nweb-frontend-5b4d7f8c9-2x7kp    15m          128Mi\nbackend-api-7d9e4c1a2-9m3lp     45m          256Mi\nprometheus-k8s-0                120m         512Mi")
            elif "top" in args and "nodes" in args:
                return make_prompt("NAME          CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%\nnode-master   150m         7%     1850Mi          45%\nnode-worker1  320m         16%    3400Mi          82%")
            return make_prompt("kubectl CLI (simulated monitoring context)")

        if cmd == "docker":
            if "stats" in args:
                return make_prompt("CONTAINER ID   NAME         CPU %     MEM USAGE / LIMIT     MEM %     NET I/O\n9a8b7c6d5e4f   prometheus   1.25%     145MiB / 2GiB         7.08%     1.2MB / 8.4MB\n1a2b3c4d5e6f   grafana      0.85%     85MiB / 2GiB          4.15%     450kB / 1.1MB\n3f4e5d6c7b8a   cadvisor     2.10%     64MiB / 2GiB          3.12%     8.9MB / 12.1MB")
            return make_prompt("Docker CLI (simulated monitoring context)")

        if cmd == "curl":
            import json
            url_target = " ".join(args).lower()
            if "3000/api/health" in url_target:
                return make_prompt('{"database": "ok", "version": "10.0.0", "commit": "v10.0.0"}')
            elif "3000/api/datasources" in url_target:
                return make_prompt(json.dumps([{"id": 1, "name": "Prometheus", "type": "prometheus", "url": "http://localhost:9090", "isDefault": True}], indent=2))
            elif "9100/metrics" in url_target:
                return make_prompt("# HELP node_cpu_seconds_total Seconds the CPUs spent in each mode.\n# TYPE node_cpu_seconds_total counter\nnode_cpu_seconds_total{cpu=\"0\",mode=\"idle\"} 142589.12\nnode_memory_MemAvailable_bytes 4294967296")
            elif "8080/metrics" in url_target:
                return make_prompt("# HELP container_cpu_usage_seconds_total Cumulative cpu time consumed\n# TYPE container_cpu_usage_seconds_total counter\ncontainer_cpu_usage_seconds_total{name=\"web\"} 45.12")
            elif "9090/api/v1/targets" in url_target:
                return make_prompt(json.dumps({"status": "success", "data": {"activeTargets": [{"discoveredLabels": {"__address__": "localhost:9090"}, "health": "up"}]}}, indent=2))
            elif "9090/api/v1/query" in url_target:
                return make_prompt(json.dumps({"status": "success", "data": {"resultType": "vector", "result": [{"metric": {"__name__": "process_cpu_seconds_total"}, "value": [1680000000, "0.045"]}]}}, indent=2))
            elif "9090/api/v1/rules" in url_target:
                return make_prompt(json.dumps({"status": "success", "data": {"groups": [{"name": "example_alerts", "rules": [{"name": "HighCPUUsage", "state": "firing"}]}]}}, indent=2))
            elif "9090/api/v1/status/buildinfo" in url_target:
                return make_prompt(json.dumps({"status": "success", "data": {"version": "2.45.0", "revision": "bb7a27", "goVersion": "go1.20"}}, indent=2))
            elif "9090/metrics" in url_target:
                return make_prompt("# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds.\n# TYPE process_cpu_seconds_total counter\nprocess_cpu_seconds_total 12.45")
            return make_prompt("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nPrometheus Monitoring Engine Operational.")

        return super().execute_command(cmd_line)


class MonitoringRuntime:
    """
    Manages isolated host-based workspace directories for Monitoring sandbox tasks.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"monitoring-{session_id}")
        )
        os.makedirs(session_dir, exist_ok=True)
        try:
            with open(os.path.join(session_dir, "prometheus.yml"), "w") as f:
                f.write(
                    "global:\n"
                    "  scrape_interval: 15s\n"
                    "  evaluation_interval: 15s\n"
                    "scrape_configs:\n"
                    "  - job_name: 'prometheus'\n"
                    "    static_configs:\n"
                    "      - targets: ['localhost:9090']\n"
                )
            with open(os.path.join(session_dir, "alertmanager.yml"), "w") as f:
                f.write(
                    "global:\n"
                    "  resolve_timeout: 5m\n"
                    "route:\n"
                    "  receiver: 'default-receiver'\n"
                    "receivers:\n"
                    "  - name: 'default-receiver'\n"
                )
            with open(os.path.join(session_dir, "rules.yml"), "w") as f:
                f.write(
                    "groups:\n"
                    "  - name: example_alerts\n"
                    "    rules:\n"
                    "      - alert: HighCPUUsage\n"
                    "        expr: rate(process_cpu_seconds_total[5m]) > 0.8\n"
                    "        for: 2m\n"
                )
            return {"container_id": f"monitoring-{session_id}", "status": "running", "mode": "monitoring"}
        except Exception as e:
            logger.error(f"MonitoringRuntime failed to initialize workspace: {e}")
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"monitoring-{session_id}")
        )
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to remove Monitoring session directory {session_dir}: {e}")


class AzureShell(GitShell):
    """
    A real host-based subshell that executes basic CLI utilities and
    simulates Azure CLI (az) commands inside the session's workspace.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"azure-{session_id}")
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.cwd = "/"
        self.history = []
        self.azure_state = {
            "groups": [],
            "vms": [],
            "vnets": [],
            "subnets": [],
            "storage_accounts": [],
            "blobs": {},
            "sql_servers": [],
            "sql_dbs": [],
            "load_balancers": [],
            "vmss": [],
            "alerts": [],
            "nsgs": [],
            "nsg_rules": []
        }

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
            return f"{output_text}{suffix}student@devlab-azure:$ "

        # Whitelist safe commands (including az, ssh, curl, terraform)
        azure_cmds = ["az", "ssh", "curl", "terraform"]
        if cmd not in ["git", "ls", "cat", "echo", "touch", "mkdir", "rm", "pwd", "clear"] + azure_cmds:
            return make_prompt(f"bash: {cmd}: command not allowed in Azure labs.")

        if cmd == "pwd":
            return make_prompt("/")

        if cmd == "terraform":
            if not args:
                return make_prompt("Usage: terraform <subcommand> [options]")
            sub = args[0]
            if sub == "init":
                dot_tf = os.path.join(self.base_dir, ".terraform")
                os.makedirs(dot_tf, exist_ok=True)
                return make_prompt("Initializing provider plugins...\n- Sourced hashicorp/azurerm (simulated)\nTerraform successfully initialized!")
            elif sub == "plan":
                return make_prompt("Plan: 8 to add, 0 to change, 0 to destroy.")
            elif sub == "apply":
                state_file = os.path.join(self.base_dir, "terraform.tfstate")
                with open(state_file, "w") as sf:
                    sf.write('{"version": 4, "resources": []}')
                return make_prompt("Apply complete! Resources: 8 added, 0 changed, 0 destroyed.")

        if cmd == "ssh":
            return make_prompt("Connection to 127.0.0.1 closed.\r\nstudent@devlab-azure:$ ")

        if cmd == "curl":
            return make_prompt("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nWelcome to Azure Production Web App!")

        if cmd == "az":
            if not args:
                return make_prompt("Usage: az [group | vm | network | storage | sql | monitor | account] [subcommand]")

            sub = args[0]
            if sub == "--version":
                return make_prompt("azure-cli/2.50.0 Python/3.11.5 Windows/10 azure-core/1.28.0")

            if sub == "account":
                import json
                return make_prompt(json.dumps([
                    {
                        "id": "00000000-0000-0000-0000-000000000000",
                        "name": "DevLab Azure Subscription",
                        "state": "Enabled",
                        "user": {"name": "student@devlab.io", "type": "user"}
                    }
                ], indent=4))

            if sub == "group":
                import json
                action = args[1] if len(args) > 1 else ""
                if action == "create":
                    rg_name = "devlab-rg"
                    if "--name" in args:
                        rg_name = args[args.index("--name") + 1]
                    self.azure_state["groups"].append(rg_name)
                    return make_prompt(json.dumps({
                        "id": f"/subscriptions/0000/resourceGroups/{rg_name}",
                        "location": "eastus",
                        "name": rg_name,
                        "properties": {"provisioningState": "Succeeded"}
                    }, indent=4))
                elif action == "list":
                    rg_list = []
                    for g in self.azure_state["groups"]:
                        rg_list.append({
                            "id": f"/subscriptions/0000/resourceGroups/{g}",
                            "location": "eastus",
                            "name": g,
                            "properties": {"provisioningState": "Succeeded"}
                        })
                    return make_prompt(json.dumps(rg_list, indent=4))

            if sub == "vm":
                import json
                action = args[1] if len(args) > 1 else ""
                if action == "create":
                    vm_name = "devlab-vm"
                    if "--name" in args:
                        vm_name = args[args.index("--name") + 1]
                    self.azure_state["vms"].append(vm_name)
                    return make_prompt(json.dumps({
                        "fqdns": "",
                        "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Compute/virtualMachines/{vm_name}",
                        "location": "eastus",
                        "macAddress": "00-0D-3A-1B-2C-3D",
                        "powerState": "VM running",
                        "privateIpAddress": "10.0.1.4",
                        "publicIpAddress": "52.170.1.1",
                        "resourceGroup": "devlab-rg"
                    }, indent=4))
                elif action == "list":
                    vms_list = []
                    for v in self.azure_state["vms"]:
                        vms_list.append({
                            "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Compute/virtualMachines/{v}",
                            "name": v,
                            "powerState": "VM running",
                            "resourceGroup": "devlab-rg"
                        })
                    return make_prompt(json.dumps(vms_list, indent=4))

            if sub == "network":
                import json
                service = args[1] if len(args) > 1 else ""
                action = args[2] if len(args) > 2 else ""
                if service == "vnet":
                    if action == "create":
                        vnet_name = "devlab-vnet"
                        if "--name" in args:
                            vnet_name = args[args.index("--name") + 1]
                        self.azure_state["vnets"].append(vnet_name)
                        return make_prompt(json.dumps({
                            "newVNet": {
                                "addressSpace": {"addressPrefixes": ["10.0.0.0/16"]},
                                "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Network/virtualNetworks/{vnet_name}",
                                "name": vnet_name,
                                "provisioningState": "Succeeded"
                            }
                        }, indent=4))
                    elif action == "subnet" and len(args) > 3 and args[3] == "create":
                        subnet_name = "devlab-subnet"
                        if "--name" in args:
                            subnet_name = args[args.index("--name") + 1]
                        self.azure_state["subnets"].append(subnet_name)
                        return make_prompt(json.dumps({
                            "addressPrefix": "10.0.1.0/24",
                            "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Network/virtualNetworks/devlab-vnet/subnets/{subnet_name}",
                            "name": subnet_name,
                            "provisioningState": "Succeeded"
                        }, indent=4))
                elif service == "lb":
                    if action == "create":
                        lb_name = "devlab-lb"
                        if "--name" in args:
                            lb_name = args[args.index("--name") + 1]
                        self.azure_state["load_balancers"].append(lb_name)
                        return make_prompt(json.dumps({
                            "LoadBalancer": {
                                "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Network/loadBalancers/{lb_name}",
                                "name": lb_name,
                                "provisioningState": "Succeeded"
                            }
                        }, indent=4))
                elif service == "nsg":
                    if action == "create":
                        nsg_name = "devlab-nsg"
                        if "--name" in args:
                            nsg_name = args[args.index("--name") + 1]
                        self.azure_state["nsgs"].append(nsg_name)
                        return make_prompt(json.dumps({
                            "NewNSG": {
                                "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Network/networkSecurityGroups/{nsg_name}",
                                "name": nsg_name,
                                "provisioningState": "Succeeded"
                            }
                        }, indent=4))
                    elif action == "rule" and len(args) > 3 and args[3] == "create":
                        rule_name = "AllowHTTP"
                        if "--name" in args:
                            rule_name = args[args.index("--name") + 1]
                        self.azure_state["nsg_rules"].append(rule_name)
                        return make_prompt(json.dumps({
                            "access": "Allow",
                            "name": rule_name,
                            "priority": 100,
                            "provisioningState": "Succeeded"
                        }, indent=4))

            if sub == "storage":
                import json
                service = args[1] if len(args) > 1 else ""
                action = args[2] if len(args) > 2 else ""
                if service == "account":
                    if action == "create":
                        acc_name = "devlabstorage"
                        if "--name" in args:
                            acc_name = args[args.index("--name") + 1]
                        self.azure_state["storage_accounts"].append(acc_name)
                        os.makedirs(os.path.join(self.base_dir, acc_name), exist_ok=True)
                        return make_prompt(json.dumps({
                            "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Storage/storageAccounts/{acc_name}",
                            "name": acc_name,
                            "primaryEndpoints": {"blob": f"https://{acc_name}.blob.core.windows.net/"},
                            "provisioningState": "Succeeded"
                        }, indent=4))
                    elif action == "list":
                        acc_list = []
                        for sa in self.azure_state["storage_accounts"]:
                            acc_list.append({
                                "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Storage/storageAccounts/{sa}",
                                "name": sa,
                                "provisioningState": "Succeeded"
                            })
                        return make_prompt(json.dumps(acc_list, indent=4))
                elif service == "blob":
                    if action == "upload":
                        container = "artifacts"
                        if "--container-name" in args:
                            container = args[args.index("--container-name") + 1]
                        file_src = ""
                        if "--file" in args:
                            file_src = args[args.index("--file") + 1]
                        blob_name = file_src
                        if "--name" in args:
                            blob_name = args[args.index("--name") + 1]
                        if container not in self.azure_state["blobs"]:
                            self.azure_state["blobs"][container] = []
                        self.azure_state["blobs"][container].append(blob_name)
                        os.makedirs(os.path.join(self.base_dir, container), exist_ok=True)
                        src_path = os.path.join(self.base_dir, file_src)
                        dest_path = os.path.join(self.base_dir, container, blob_name)
                        if os.path.exists(src_path):
                            shutil.copy(src_path, dest_path)
                        else:
                            with open(dest_path, "w") as df:
                                df.write("Simulated Azure Blob content")
                        return make_prompt(json.dumps({"finished": True, "name": blob_name}, indent=4))

            if sub == "sql":
                import json
                service = args[1] if len(args) > 1 else ""
                action = args[2] if len(args) > 2 else ""
                if service == "server" and action == "create":
                    srv_name = "devlab-sqlserver"
                    if "--name" in args:
                        srv_name = args[args.index("--name") + 1]
                    self.azure_state["sql_servers"].append(srv_name)
                    return make_prompt(json.dumps({
                        "fullyQualifiedDomainName": f"{srv_name}.database.windows.net",
                        "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Sql/servers/{srv_name}",
                        "name": srv_name,
                        "state": "Ready"
                    }, indent=4))
                elif service == "db" and action == "create":
                    db_name = "devlab-db"
                    if "--name" in args:
                        db_name = args[args.index("--name") + 1]
                    self.azure_state["sql_dbs"].append(db_name)
                    return make_prompt(json.dumps({
                        "databaseId": "00000000-0000-0000-0000-000000000000",
                        "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Sql/servers/devlab-sqlserver/databases/{db_name}",
                        "name": db_name,
                        "status": "Online"
                    }, indent=4))

            if sub == "vmss":
                import json
                action = args[1] if len(args) > 1 else ""
                if action == "create":
                    vmss_name = "devlab-vmss"
                    if "--name" in args:
                        vmss_name = args[args.index("--name") + 1]
                    self.azure_state["vmss"].append(vmss_name)
                    return make_prompt(json.dumps({
                        "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Compute/virtualMachineScaleSets/{vmss_name}",
                        "name": vmss_name,
                        "provisioningState": "Succeeded"
                    }, indent=4))

            if sub == "monitor":
                import json
                service = args[1] if len(args) > 1 else ""
                if service == "metrics":
                    action = args[3] if len(args) > 3 else ""
                    if action == "create":
                        alert_name = "devlab-cpu-alert"
                        if "--name" in args:
                            alert_name = args[args.index("--name") + 1]
                        self.azure_state["alerts"].append(alert_name)
                        return make_prompt(json.dumps({
                            "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Insights/metricAlerts/{alert_name}",
                            "name": alert_name,
                            "properties": {"enabled": True}
                        }, indent=4))
                    elif action == "list":
                        alert_list = []
                        for a in self.azure_state["alerts"]:
                            alert_list.append({
                                "id": f"/subscriptions/0000/resourceGroups/devlab-rg/providers/Microsoft.Insights/metricAlerts/{a}",
                                "name": a,
                                "properties": {"enabled": True}
                            })
                        return make_prompt(json.dumps(alert_list, indent=4))

            return make_prompt("Azure operation executed successfully (simulated).")

        return super().execute_command(cmd_line)


class AzureRuntime:
    """
    Manages isolated host-based workspace directories for Azure sandbox tasks.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"azure-{session_id}")
        )
        os.makedirs(session_dir, exist_ok=True)
        try:
            with open(os.path.join(session_dir, "playbook.yml"), "w") as f:
                f.write(
                    "---\n"
                    "- name: Welcome\n"
                    "  hosts: all\n"
                    "  tasks:\n"
                    "    - name: Print welcome\n"
                    "      debug:\n"
                    "        msg: \"Welcome to Azure!\"\n"
                )
            with open(os.path.join(session_dir, "main.tf"), "w") as f:
                f.write(
                    "# Welcome to Terraform on Azure!\n"
                    "provider \"azurerm\" {\n"
                    "  features {}\n"
                    "}\n"
                )
            return {"container_id": f"azure-{session_id}", "status": "running", "mode": "azure"}
        except Exception as e:
            logger.error(f"AzureRuntime failed to initialize workspace: {e}")
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"azure-{session_id}")
        )
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to remove Azure session directory {session_dir}: {e}")


class AWSShell(GitShell):
    """
    A real host-based subshell that executes basic CLI utilities and
    simulates AWS CLI commands inside the session's workspace.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"aws-{session_id}")
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.cwd = "/"
        self.history = []
        self.aws_state = {
            "users": [],
            "vpcs": [],
            "subnets": [],
            "security_groups": [],
            "instances": [],
            "buckets": {},
            "rds": [],
            "load_balancers": [],
            "asg": [],
            "alarms": []
        }

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
            return f"{output_text}{suffix}student@devlab-aws:$ "

        # Whitelist safe commands (including aws, ssh, curl, terraform)
        aws_cmds = ["aws", "ssh", "curl", "terraform"]
        if cmd not in ["git", "ls", "cat", "echo", "touch", "mkdir", "rm", "pwd", "clear"] + aws_cmds:
            return make_prompt(f"bash: {cmd}: command not allowed in AWS labs.")

        if cmd == "pwd":
            return make_prompt("/")

        # Check if actual command exists and run, or fallback to simulated behavior
        actual_bin = shutil.which(cmd)
        
        # If running terraform init/plan/apply in AWS workspace, support simulation
        if cmd == "terraform":
            if not args:
                return make_prompt("Usage: terraform <subcommand> [options]")
            sub = args[0]
            if sub == "init":
                dot_tf = os.path.join(self.base_dir, ".terraform")
                os.makedirs(dot_tf, exist_ok=True)
                return make_prompt("Initializing provider plugins...\n- Sourced hashicorp/aws (simulated)\nTerraform successfully initialized!")
            elif sub == "plan":
                return make_prompt("Plan: 8 to add, 0 to change, 0 to destroy.")
            elif sub == "apply":
                state_file = os.path.join(self.base_dir, "terraform.tfstate")
                with open(state_file, "w") as sf:
                    sf.write('{"version": 4, "resources": []}')
                return make_prompt("Apply complete! Resources: 8 added, 0 changed, 0 destroyed.")

        if cmd == "ssh":
            return make_prompt("Connection to 127.0.0.1 closed.\r\nstudent@devlab-aws:$ ")

        if cmd == "curl":
            return make_prompt("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\nWelcome to AWS Production Web App!")

        if cmd == "aws":
            if not args:
                return make_prompt("Usage: aws [options] <command> <subcommand> [parameters]")
            
            sub = args[0]
            if sub == "--version":
                return make_prompt("aws-cli/2.15.0 Python/3.11.5 Windows/10 botocore/2.4.5")
            
            if len(args) < 2 and sub != "configure" and sub != "s3":
                return make_prompt(f"aws {sub}: missing subcommands parameters.")

            if sub == "configure":
                if args[1:] and args[1] == "list":
                    output = (
                        "      Name                    Value             Type    Location\r\n"
                        "      ----                    -----             ----    --------\r\n"
                        "   profile                <not set>             None    None\r\n"
                        "access_key     ****************t5a4      shared-credentials-file\r\n"
                        "secret_key     ****************T2e9      shared-credentials-file\r\n"
                        "    region                us-east-1      config-file    ~/.aws/config"
                    )
                    return make_prompt(output)
                return make_prompt("Configured AWS Access Credentials saved successfully (simulated).")

            if sub == "iam":
                action = args[1]
                if action == "create-user":
                    user_name = "devlab-admin"
                    if "--user-name" in args:
                        user_idx = args.index("--user-name") + 1
                        if user_idx < len(args):
                            user_name = args[user_idx]
                    self.aws_state["users"].append(user_name)
                    output_json = {
                        "User": {
                            "Path": "/",
                            "UserName": user_name,
                            "UserId": "AIDA1234567890EXAMPLE",
                            "Arn": f"arn:aws:iam::123456789012:user/{user_name}",
                            "CreateDate": "2026-07-19T20:00:00Z"
                        }
                    }
                    import json
                    return make_prompt(json.dumps(output_json, indent=4))
                elif action == "list-users":
                    users_list = []
                    for u in self.aws_state["users"]:
                        users_list.append({
                            "Path": "/",
                            "UserName": u,
                            "UserId": "AIDA1234567890EXAMPLE",
                            "Arn": f"arn:aws:iam::123456789012:user/{u}",
                            "CreateDate": "2026-07-19T20:00:00Z"
                        })
                    import json
                    return make_prompt(json.dumps({"Users": users_list}, indent=4))

            if sub == "ec2":
                action = args[1]
                if action == "create-vpc":
                    cidr = "10.0.0.0/16"
                    if "--cidr-block" in args:
                        cidr_idx = args.index("--cidr-block") + 1
                        if cidr_idx < len(args):
                            cidr = args[cidr_idx]
                    vpc_id = f"vpc-{len(self.aws_state['vpcs']):08d}"
                    self.aws_state["vpcs"].append({"id": vpc_id, "cidr": cidr})
                    output_json = {
                        "Vpc": {
                            "CidrBlock": cidr,
                            "VpcId": vpc_id,
                            "State": "available"
                        }
                    }
                    import json
                    return make_prompt(json.dumps(output_json, indent=4))
                
                elif action == "create-subnet":
                    cidr = "10.0.1.0/24"
                    if "--cidr-block" in args:
                        cidr_idx = args.index("--cidr-block") + 1
                        if cidr_idx < len(args):
                            cidr = args[cidr_idx]
                    subnet_id = f"subnet-{len(self.aws_state['subnets']):08d}"
                    self.aws_state["subnets"].append({"id": subnet_id, "cidr": cidr})
                    output_json = {
                        "Subnet": {
                            "CidrBlock": cidr,
                            "SubnetId": subnet_id,
                            "State": "available"
                        }
                    }
                    import json
                    return make_prompt(json.dumps(output_json, indent=4))

                elif action == "create-security-group":
                    sg_name = "devlab-sg"
                    if "--group-name" in args:
                        sg_idx = args.index("--group-name") + 1
                        if sg_idx < len(args):
                            sg_name = args[sg_idx]
                    sg_id = f"sg-{len(self.aws_state['security_groups']):08d}"
                    self.aws_state["security_groups"].append({"id": sg_id, "name": sg_name})
                    import json
                    return make_prompt(json.dumps({"GroupId": sg_id}, indent=4))

                elif action == "authorize-security-group-ingress":
                    return make_prompt("Security Group ingress rule successfully authorized (simulated).")

                elif action == "run-instances":
                    inst_id = f"i-{len(self.aws_state['instances']):08d}"
                    self.aws_state["instances"].append(inst_id)
                    output_json = {
                        "Instances": [
                            {
                                "InstanceId": inst_id,
                                "State": {
                                    "Code": 16,
                                    "Name": "running"
                                },
                                "PublicDnsName": f"ec2-127-0-0-1.compute-1.amazonaws.com"
                            }
                        ]
                    }
                    import json
                    return make_prompt(json.dumps(output_json, indent=4))

                elif action == "describe-instances":
                    insts = []
                    for inst in self.aws_state["instances"]:
                        insts.append({
                            "InstanceId": inst,
                            "State": {
                                "Code": 16,
                                "Name": "running"
                            },
                            "PublicDnsName": f"ec2-127-0-0-1.compute-1.amazonaws.com"
                        })
                    import json
                    return make_prompt(json.dumps({"Reservations": [{"Instances": insts}]}, indent=4))

            if sub == "s3":
                s3_cmd = args[1]
                if s3_cmd == "mb":
                    bucket = args[2] if len(args) > 2 else "s3://devlab-bucket"
                    bucket_name = bucket.replace("s3://", "")
                    self.aws_state["buckets"][bucket_name] = []
                    os.makedirs(os.path.join(self.base_dir, bucket_name), exist_ok=True)
                    return make_prompt(f"make_bucket: {bucket}")
                elif s3_cmd == "cp":
                    src = args[2] if len(args) > 2 else ""
                    dest = args[3] if len(args) > 3 else ""
                    dest_clean = dest.replace("s3://", "")
                    dest_parts = dest_clean.split("/")
                    bucket_name = dest_parts[0]
                    if len(dest_parts) > 1 and dest_parts[1]:
                        file_name = dest_parts[1]
                    else:
                        file_name = os.path.basename(src)
                    if bucket_name in self.aws_state["buckets"]:
                        self.aws_state["buckets"][bucket_name].append(file_name)
                        src_path = os.path.join(self.base_dir, src)
                        dest_path = os.path.join(self.base_dir, bucket_name, file_name)
                        if os.path.exists(src_path):
                            shutil.copy(src_path, dest_path)
                        else:
                            with open(dest_path, "w") as df:
                                df.write("Simulated S3 file content")
                    return make_prompt(f"upload: {src} to {dest}")
                elif s3_cmd == "ls":
                    output = []
                    for b in self.aws_state["buckets"]:
                        output.append(f"2026-07-19 20:00:00 {b}")
                    return make_prompt("\r\n".join(output) if output else "No buckets found.")

            if sub == "rds":
                action = args[1]
                if action == "create-db-instance":
                    db_id = "devlab-db"
                    if "--db-instance-identifier" in args:
                        db_idx = args.index("--db-instance-identifier") + 1
                        if db_idx < len(args):
                            db_id = args[db_idx]
                    self.aws_state["rds"].append(db_id)
                    output_json = {
                        "DBInstance": {
                            "DBInstanceIdentifier": db_id,
                            "DBInstanceClass": "db.t3.micro",
                            "Engine": "postgres",
                            "DBInstanceStatus": "creating"
                        }
                    }
                    import json
                    return make_prompt(json.dumps(output_json, indent=4))
                elif action == "describe-db-instances":
                    dbs = []
                    for db in self.aws_state["rds"]:
                        dbs.append({
                            "DBInstanceIdentifier": db,
                            "DBInstanceClass": "db.t3.micro",
                            "Engine": "postgres",
                            "DBInstanceStatus": "available"
                        })
                    import json
                    return make_prompt(json.dumps({"DBInstances": dbs}, indent=4))

            if sub == "elbv2":
                action = args[1]
                if action == "create-load-balancer":
                    lb_name = "devlab-alb"
                    if "--name" in args:
                        lb_idx = args.index("--name") + 1
                        if lb_idx < len(args):
                            lb_name = args[lb_idx]
                    self.aws_state["load_balancers"].append(lb_name)
                    output_json = {
                        "LoadBalancers": [
                            {
                                "LoadBalancerName": lb_name,
                                "DNSName": "devlab-alb-123456789.us-east-1.elb.amazonaws.com",
                                "State": {"Code": "active"}
                            }
                        ]
                    }
                    import json
                    return make_prompt(json.dumps(output_json, indent=4))

            if sub == "autoscaling":
                action = args[1]
                if action == "create-auto-scaling-group":
                    asg_name = "devlab-asg"
                    if "--auto-scaling-group-name" in args:
                        asg_idx = args.index("--auto-scaling-group-name") + 1
                        if asg_idx < len(args):
                            asg_name = args[asg_idx]
                    self.aws_state["asg"].append(asg_name)
                    return make_prompt("Auto Scaling Group successfully created (simulated).")

            if sub == "cloudwatch":
                action = args[1]
                if action == "put-metric-alarm":
                    alarm_name = "devlab-cpu-alarm"
                    if "--alarm-name" in args:
                        alarm_idx = args.index("--alarm-name") + 1
                        if alarm_idx < len(args):
                            alarm_name = args[alarm_idx]
                    self.aws_state["alarms"].append(alarm_name)
                    return make_prompt("CloudWatch Alarm successfully created (simulated).")
                elif action == "describe-alarms":
                    alarms_list = []
                    for al in self.aws_state["alarms"]:
                        alarms_list.append({
                            "AlarmName": al,
                            "MetricName": "CPUUtilization",
                            "StateValue": "OK"
                        })
                    import json
                    return make_prompt(json.dumps({"MetricAlarms": alarms_list}, indent=4))

            return make_prompt("AWS operation executed successfully (simulated).")

        return super().execute_command(cmd_line)


class AWSRuntime:
    """
    Manages isolated host-based workspace directories for AWS sandbox tasks.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"aws-{session_id}")
        )
        os.makedirs(session_dir, exist_ok=True)
        try:
            with open(os.path.join(session_dir, "playbook.yml"), "w") as f:
                f.write(
                    "---\n"
                    "- name: Welcome\n"
                    "  hosts: all\n"
                    "  tasks:\n"
                    "    - name: Print welcome\n"
                    "      debug:\n"
                    "        msg: \"Welcome to Ansible!\"\n"
                )
            with open(os.path.join(session_dir, "main.tf"), "w") as f:
                f.write(
                    "# Welcome to Terraform on AWS!\n"
                    "provider \"aws\" {\n"
                    "  region = \"us-east-1\"\n"
                    "}\n"
                )
            return {"container_id": f"aws-{session_id}", "status": "running", "mode": "aws"}
        except Exception as e:
            logger.error(f"AWSRuntime failed to initialize workspace: {e}")
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"aws-{session_id}")
        )
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to remove AWS session directory {session_dir}: {e}")


class AnsibleShell(GitShell):
    """
    A real host-based subshell that executes basic CLI utilities and
    simulates Ansible commands inside the session's workspace.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"ansible-{session_id}")
        )
        os.makedirs(self.base_dir, exist_ok=True)
        self.cwd = "/"
        self.history = []

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
            return f"{output_text}{suffix}student@devlab-ansible:$ "

        # Whitelist safe commands (including ansible tools)
        ansible_cmds = ["ansible", "ansible-playbook", "ansible-inventory", "ansible-galaxy", "ansible-doc"]
        if cmd not in ["git", "ls", "cat", "echo", "touch", "mkdir", "rm", "pwd", "clear"] + ansible_cmds:
            return make_prompt(f"bash: {cmd}: command not allowed in Ansible labs.")

        if cmd == "pwd":
            return make_prompt("/")

        # Check if actual Ansible is installed on the host
        actual_bin = shutil.which(cmd)
        if actual_bin:
            try:
                res = subprocess.run(
                    cmd_line,
                    cwd=self.base_dir,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = res.stdout
                if res.stderr:
                    output += "\n" + res.stderr
                output_formatted = output.replace("\r\n", "\n").replace("\n", "\r\n")
                return make_prompt(output_formatted)
            except subprocess.TimeoutExpired:
                return make_prompt("Error: Command execution timed out.")
            except Exception as e:
                return make_prompt(f"Error: Command execution failed: {e}")

        # Simulated Fallback Behavior
        if cmd == "ansible":
            if not args:
                return make_prompt("Usage: ansible <host-pattern> [options]")
            
            hosts_file = os.path.join(self.base_dir, "hosts")
            if "-i" in args:
                hosts_idx = args.index("-i") + 1
                if hosts_idx < len(args):
                    hosts_file = os.path.normpath(os.path.join(self.base_dir, args[hosts_idx]))
            
            if not os.path.exists(hosts_file):
                return make_prompt(f"ERROR! The pathway {os.path.basename(hosts_file)} does not exist")

            if "-m" in args:
                module_idx = args.index("-m") + 1
                module_name = args[module_idx] if module_idx < len(args) else ""
                
                if module_name == "ping":
                    output = (
                        "localhost | SUCCESS => {\r\n"
                        "    \"changed\": false,\r\n"
                        "    \"ping\": \"pong\"\r\n"
                        "}"
                    )
                    return make_prompt(output)
                elif module_name in ["shell", "command"]:
                    cmd_arg = ""
                    if "-a" in args:
                        arg_idx = args.index("-a") + 1
                        if arg_idx < len(args):
                            cmd_arg = args[arg_idx].strip("\"'")
                    
                    if cmd_arg == "uptime":
                        output = (
                            "localhost | CHANGED | rc=0 >>\r\n"
                            " 11:49:15 up 2 days, 3 hours, 1 user, load average: 0.05, 0.03, 0.01"
                        )
                        return make_prompt(output)
                    else:
                        output = f"localhost | SUCCESS | rc=0 >>\r\nExecuted ad-hoc command: {cmd_arg}"
                        return make_prompt(output)

            return make_prompt("localhost | SUCCESS => {\n    \"changed\": false\n}")

        if cmd == "ansible-playbook":
            if not args:
                return make_prompt("Usage: ansible-playbook playbook.yml [options]")
            
            playbook_name = args[0]
            for arg in args:
                if arg.endswith(".yml") or arg.endswith(".yaml"):
                    playbook_name = arg
                    break
                    
            playbook_path = os.path.join(self.base_dir, playbook_name)
            if not os.path.exists(playbook_path):
                return make_prompt(f"ERROR! The playbook file {playbook_name} could not be found.")

            if "--syntax-check" in args:
                try:
                    import yaml
                    with open(playbook_path, "r", encoding="utf-8") as f:
                        yaml.safe_load(f)
                    return make_prompt(f"\r\nplaybook: {playbook_name}")
                except Exception as ye:
                    return make_prompt(f"ERROR! Playbook syntax check failed:\n{ye}")

            try:
                import yaml
                with open(playbook_path, "r", encoding="utf-8") as f:
                    playbook_data = yaml.safe_load(f) or []
            except Exception as e:
                return make_prompt(f"ERROR! Failed to parse playbook YAML: {e}")

            if not isinstance(playbook_data, list):
                if isinstance(playbook_data, dict):
                    playbook_data = [playbook_data]
                else:
                    return make_prompt("ERROR! Playbook must be a list of plays.")

            log_lines = []
            for play in playbook_data:
                play_name = play.get("name", "Unnamed Play")
                log_lines.append(f"\r\nPLAY [{play_name}] *********************************************************************")
                log_lines.append("\r\nTASK [Gathering Facts] *********************************************************")
                log_lines.append("ok: [localhost]")

                roles = play.get("roles", [])
                if isinstance(roles, list):
                    for role in roles:
                        role_name = role if isinstance(role, str) else role.get("role", "unknown")
                        role_task_path = os.path.join(self.base_dir, "roles", role_name, "tasks", "main.yml")
                        if os.path.exists(role_task_path):
                            log_lines.append(f"\r\nTASK [{role_name} : Run role task] ******************************************************")
                            log_lines.append("changed: [localhost]")

                tasks = play.get("tasks", [])
                if isinstance(tasks, list):
                    for task in tasks:
                        task_name = task.get("name", "Run task module")
                        log_lines.append(f"\r\nTASK [{task_name}] ***********************************************************")
                        
                        if "template" in task:
                            tmpl_info = task["template"]
                            src = tmpl_info.get("src")
                            dest = tmpl_info.get("dest")
                            if src and dest:
                                src_path = os.path.join(self.base_dir, src)
                                dest_path = os.path.join(self.base_dir, dest)
                                if os.path.exists(src_path):
                                    with open(src_path, "r", encoding="utf-8") as sf:
                                        content = sf.read()
                                    val_port = "8080"
                                    content_rendered = content.replace("{{ app_port }}", val_port).replace("{{app_port}}", val_port)
                                    with open(dest_path, "w", encoding="utf-8") as df:
                                        df.write(content_rendered)
                            log_lines.append("changed: [localhost]")
                        else:
                            log_lines.append("changed: [localhost]")
                            
            log_lines.append("\r\nPLAY RECAP *********************************************************************")
            log_lines.append("localhost                  : ok=3    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0")
            return make_prompt("\r\n".join(log_lines))

        if cmd == "ansible-inventory":
            if not args:
                return make_prompt("Usage: ansible-inventory -i hosts [options]")
            hosts_file = "hosts"
            if "-i" in args:
                hosts_idx = args.index("-i") + 1
                if hosts_idx < len(args):
                    hosts_file = args[hosts_idx]
            
            hosts_path = os.path.join(self.base_dir, hosts_file)
            if not os.path.exists(hosts_path):
                return make_prompt(f"ERROR! Inventory file {hosts_file} could not be found.")

            if "--list" in args:
                output = (
                    "{\r\n"
                    "    \"_meta\": {\r\n"
                    "        \"hostvars\": {}\r\n"
                    "    },\r\n"
                    "    \"all\": {\r\n"
                    "        \"children\": [\r\n"
                    "            \"ungrouped\",\r\n"
                    "            \"webservers\"\r\n"
                    "        ]\r\n"
                    "    },\r\n"
                    "    \"webservers\": {\r\n"
                    "        \"hosts\": [\r\n"
                    "            \"localhost\"\r\n"
                    "        ]\r\n"
                    "    }\r\n"
                    "}"
                )
                return make_prompt(output)
            return make_prompt("localhost")

        if cmd == "ansible-galaxy":
            if len(args) < 2:
                return make_prompt("Usage: ansible-galaxy [role|collection] [action] [options]")
            
            sub = args[0]
            action = args[1]
            if sub == "role" or action == "init":
                role_name = args[2] if len(args) > 2 else args[-1]
                role_dir = os.path.join(self.base_dir, role_name)
                os.makedirs(os.path.join(role_dir, "tasks"), exist_ok=True)
                os.makedirs(os.path.join(role_dir, "vars"), exist_ok=True)
                os.makedirs(os.path.join(role_dir, "handlers"), exist_ok=True)
                os.makedirs(os.path.join(role_dir, "templates"), exist_ok=True)
                
                with open(os.path.join(role_dir, "tasks", "main.yml"), "w") as f:
                    f.write("---\n# tasks file for " + os.path.basename(role_name) + "\n")
                
                output = f"- {os.path.basename(role_name)} was created successfully"
                return make_prompt(output)
            
            return make_prompt("ansible-galaxy operation successful")

        if cmd == "ansible-doc":
            module_name = args[0] if args else "ping"
            output = (
                f"> {module_name.upper()}    ({self.base_dir})\r\n\r\n"
                f"  This module simulates help documentation for {module_name}.\r\n"
                "  Refer to docs.ansible.com for official options definitions."
            )
            return make_prompt(output)

        return super().execute_command(cmd_line)


class AnsibleRuntime:
    """
    Manages isolated host-based workspace directories for Ansible sandbox tasks.
    """
    def create_session(self, session_id: str) -> Dict[str, Any]:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"ansible-{session_id}")
        )
        os.makedirs(session_dir, exist_ok=True)
        try:
            with open(os.path.join(session_dir, "hosts"), "w") as f:
                f.write(
                    "[webservers]\n"
                    "localhost ansible_connection=local\n"
                )
            with open(os.path.join(session_dir, "playbook.yml"), "w") as f:
                f.write(
                    "---\n"
                    "- name: DevLab Ansible Playground\n"
                    "  hosts: all\n"
                    "  tasks:\n"
                    "    - name: Ping test\n"
                    "      ping:\n"
                )
            return {"container_id": f"ansible-{session_id}", "status": "running", "mode": "ansible"}
        except Exception as e:
            logger.error(f"AnsibleRuntime failed to initialize workspace: {e}")
            return {"container_id": f"simulated-{session_id}", "status": "running", "mode": "simulated"}

    def stop_session(self, session_id: str, container_id: Optional[str] = None) -> None:
        session_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../scratch/sessions", f"ansible-{session_id}")
        )
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to remove Ansible session directory {session_dir}: {e}")


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
        self.kubernetes_runtime = KubernetesRuntime()
        self.git_runtime = GitRuntime()
        self.github_actions_runtime = GitHubActionsRuntime()
        self.cicd_runtime = CICDRuntime()
        self.jenkins_runtime = JenkinsRuntime()
        self.terraform_runtime = TerraformRuntime()
        self.ansible_runtime = AnsibleRuntime()
        self.aws_runtime = AWSRuntime()
        self.azure_runtime = AzureRuntime()
        self.monitoring_runtime = MonitoringRuntime()

    def create_lab(self, session_id: str, lab_name: str = "linux-basics") -> Dict[str, Any]:
        """
        Delegates lab initialization checks to custom Runtimes.
        """
        if "monitoring" in lab_name or "prometheus" in lab_name or "promql" in lab_name or "exporters" in lab_name or "alertmanager" in lab_name or "grafana" in lab_name:
            res = self.monitoring_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            else:
                self.simulated_sessions[session_id] = MonitoringShell(session_id)
            return res
        elif "azure" in lab_name or "resource-groups" in lab_name or "virtual-machines" in lab_name or "virtual-networks" in lab_name or "storage-accounts" in lab_name or "sql-database" in lab_name or "scale-sets" in lab_name or "azure-monitor" in lab_name:
            res = self.azure_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            else:
                self.simulated_sessions[session_id] = AzureShell(session_id)
            return res
        elif "aws" in lab_name or "iam-" in lab_name or "ec2-" in lab_name or "vpc-" in lab_name or "s3-" in lab_name or "rds-" in lab_name or "load-balancers-" in lab_name or "cloudwatch-" in lab_name:
            res = self.aws_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            else:
                self.simulated_sessions[session_id] = AWSShell(session_id)
            return res
        elif "ansible" in lab_name or "inventory-files" in lab_name or "ad-hoc-commands" in lab_name or "writing-playbooks" in lab_name or "variables-and-facts" in lab_name or "templates-and-jinja2" in lab_name or "ansible-galaxy" in lab_name or "tags-handlers-and" in lab_name:
            res = self.ansible_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            else:
                self.simulated_sessions[session_id] = AnsibleShell(session_id)
            return res
        elif "terraform" in lab_name or "variables-outputs" in lab_name or "state-management" in lab_name or "best-practices-terraform" in lab_name:
            res = self.terraform_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            else:
                self.simulated_sessions[session_id] = TerraformShell(session_id)
            return res
        elif "jenkins" in lab_name or "freestyle-jobs" in lab_name or "declarative-vs-" in lab_name or "distributed-builds" in lab_name or "credentials-and-secrets" in lab_name or "plugins-and-" in lab_name:
            res = self.jenkins_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            else:
                self.simulated_sessions[session_id] = JenkinsShell(session_id)
            return res
        elif "introduction-to-cicd" in lab_name or "continuous-" in lab_name or "building-a-complete-cicd" in lab_name or lab_name == "cicd":
            res = self.cicd_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            else:
                self.simulated_sessions[session_id] = CICDShell(session_id)
            return res
        elif "github-actions" in lab_name:
            res = self.github_actions_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            else:
                self.simulated_sessions[session_id] = GitHubActionsShell(session_id)
            return res
        elif "git-" in lab_name or lab_name == "git":
            res = self.git_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedShell(session_id)
            else:
                self.simulated_sessions[session_id] = GitShell(session_id)
            return res
        elif "kubernetes-" in lab_name or "k8s-" in lab_name:
            res = self.kubernetes_runtime.create_session(session_id)
            if res["mode"] == "simulated":
                self.simulated_sessions[session_id] = SimulatedKubernetesShell(session_id)
            return res
        elif "docker" in lab_name:
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
                    shutil.rmtree(shell.base_dir, onerror=_remove_readonly)
                except Exception as e:
                    logger.warning(f"Failed to remove directory {shell.base_dir}: {e}")

        if "monitoring" in lab_name or "prometheus" in lab_name or "promql" in lab_name or "exporters" in lab_name or "alertmanager" in lab_name or "grafana" in lab_name:
            self.monitoring_runtime.stop_session(session_id, container_id)
        elif "azure" in lab_name or "resource-groups" in lab_name or "virtual-machines" in lab_name or "virtual-networks" in lab_name or "storage-accounts" in lab_name or "sql-database" in lab_name or "scale-sets" in lab_name or "azure-monitor" in lab_name:
            self.azure_runtime.stop_session(session_id, container_id)
        elif "aws" in lab_name or "iam-" in lab_name or "ec2-" in lab_name or "vpc-" in lab_name or "s3-" in lab_name or "rds-" in lab_name or "load-balancers-" in lab_name or "cloudwatch-" in lab_name:
            self.aws_runtime.stop_session(session_id, container_id)
        elif "ansible" in lab_name or "inventory-files" in lab_name or "ad-hoc-commands" in lab_name or "writing-playbooks" in lab_name or "variables-and-facts" in lab_name or "templates-and-jinja2" in lab_name or "ansible-galaxy" in lab_name or "tags-handlers-and" in lab_name:
            self.ansible_runtime.stop_session(session_id, container_id)
        elif "terraform" in lab_name or "variables-outputs" in lab_name or "state-management" in lab_name or "best-practices-terraform" in lab_name:
            self.terraform_runtime.stop_session(session_id, container_id)
        elif "jenkins" in lab_name or "freestyle-jobs" in lab_name or "declarative-vs-" in lab_name or "distributed-builds" in lab_name or "credentials-and-secrets" in lab_name or "plugins-and-" in lab_name:
            self.jenkins_runtime.stop_session(session_id, container_id)
        elif "introduction-to-cicd" in lab_name or "continuous-" in lab_name or "building-a-complete-cicd" in lab_name or lab_name == "cicd":
            self.cicd_runtime.stop_session(session_id, container_id)
        elif "github-actions" in lab_name:
            self.github_actions_runtime.stop_session(session_id, container_id)
        elif "git-" in lab_name or lab_name == "git":
            self.git_runtime.stop_session(session_id, container_id)
        elif "kubernetes-" in lab_name or "k8s-" in lab_name:
            self.kubernetes_runtime.stop_session(session_id, container_id)
        elif "docker" in lab_name:
            self.docker_runtime.stop_session(session_id, container_id)
        else:
            self.linux_runtime.stop_session(session_id, container_id)

    def get_session_shell(self, session_id: str, lab_name: Optional[str] = None) -> Optional[SimulatedShell]:
        if session_id in self.simulated_sessions:
            return self.simulated_sessions[session_id]
        if lab_name:
            if "monitoring" in lab_name or "prometheus" in lab_name or "promql" in lab_name or "exporters" in lab_name or "alertmanager" in lab_name or "grafana" in lab_name:
                shell = MonitoringShell(session_id)
            elif "azure" in lab_name or "resource-groups" in lab_name or "virtual-machines" in lab_name or "virtual-networks" in lab_name or "storage-accounts" in lab_name or "sql-database" in lab_name or "scale-sets" in lab_name or "azure-monitor" in lab_name:
                shell = AzureShell(session_id)
            elif "aws" in lab_name or "iam-" in lab_name or "ec2-" in lab_name or "vpc-" in lab_name or "s3-" in lab_name or "rds-" in lab_name or "load-balancers-" in lab_name or "cloudwatch-" in lab_name:
                shell = AWSShell(session_id)
            elif "ansible" in lab_name or "inventory-files" in lab_name or "ad-hoc-commands" in lab_name or "writing-playbooks" in lab_name or "variables-and-facts" in lab_name or "templates-and-jinja2" in lab_name or "ansible-galaxy" in lab_name or "tags-handlers-and" in lab_name:
                shell = AnsibleShell(session_id)
            elif "terraform" in lab_name or "variables-outputs" in lab_name or "state-management" in lab_name or "best-practices-terraform" in lab_name:
                shell = TerraformShell(session_id)
            elif "jenkins" in lab_name or "freestyle-jobs" in lab_name or "declarative-vs-" in lab_name or "distributed-builds" in lab_name or "credentials-and-secrets" in lab_name or "plugins-and-" in lab_name:
                shell = JenkinsShell(session_id)
            elif "introduction-to-cicd" in lab_name or "continuous-" in lab_name or "building-a-complete-cicd" in lab_name or lab_name == "cicd":
                shell = CICDShell(session_id)
            elif "github-actions" in lab_name:
                shell = GitHubActionsShell(session_id)
            elif "git-" in lab_name or lab_name == "git":
                shell = GitShell(session_id)
            elif "kubernetes-" in lab_name or "k8s-" in lab_name:
                shell = SimulatedKubernetesShell(session_id)
            elif "docker" in lab_name:
                shell = SimulatedDockerShell(session_id)
            else:
                shell = SimulatedShell(session_id)
            self.simulated_sessions[session_id] = shell
            return shell
        return None


# Global instance
runtime_service = LabRuntimeService()
