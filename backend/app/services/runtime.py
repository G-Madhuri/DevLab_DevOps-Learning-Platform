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
