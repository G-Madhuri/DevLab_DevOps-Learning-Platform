import json
import os

base_path = "backend/app/courses/lessons"

# Load basics_data
from scratch.basics_data import basics_data

# Write basics
with open(os.path.join(base_path, "linux-command-line-basics.json"), "w", encoding="utf-8") as f:
    json.dump(basics_data, f, indent=2, ensure_ascii=False)
print("Enriched command line basics JSON.")

# Define permissions_data
permissions_data = {
  "slug": "linux-file-system-permissions",
  "title": "Linux File System & Permissions",
  "overview": {
    "introduction": [
      "In a multi-user operating system like Linux, security is built into the core design. Without a strict mechanism to control who can read, modify, or execute files, any user or running process could access sensitive configurations, read other users' private data, or corrupt the operating system itself. Linux solves this problem through its file permissions and ownership subsystem.",
      "For DevOps Engineers, managing file system permissions is a fundamental safety barrier. When deploying applications, web server processes (like Nginx) should only have read access to source files, database folders must be restricted to the database user account, and private SSH keys must be locked down to owner-only read access. Understanding how to configure access control lists prevents unauthorized processes from reading or writing configuration secrets.",
      "In this module, you will learn how to read permissions configurations outputs, modify read/write/execute bits using chmod symbolic and numeric notation, change file owners and group owners using chown/chgrp, and configure default creation masks utilizing umask."
    ],
    "what_you_will_learn": [
      "The layout of user permissions flags (Read, Write, Execute).",
      "Assigning symbolic and numeric permission modifications using chmod.",
      "Managing file ownership and group memberships utilizing chown and chgrp.",
      "Configuring security restrictions on directory access settings.",
      "Checking default file creation masks via umask."
    ],
    "prerequisites": "Completion of Linux Command Line Basics course.",
    "estimated_time": "90 mins",
    "difficulty": "Intermediate",
    "learning_outcomes": [
      "Analyze detailed metadata listings of files and directories.",
      "Apply least-privilege permission masks using symbolic and numeric chmod syntax.",
      "Manage system user account permissions using chown and chgrp.",
      "Expose umask default creations settings."
    ]
  },
  "theory": [
    {
      "title": "Linux File Permissions Bitmask",
      "definition": "A 9-bit binary representation indicating access rights for the Owner, Group, and Others.",
      "explanation": "Every file contains metadata flags detailing access states. The first letter in detailed listings represents file type (e.g. `d` for directory, `-` for regular file). The next 9 characters are grouped in three segments of 3: User/Owner (u), Group (g), and Others/World (o). Each segment has flags `r` (Read), `w` (Write), and `x` (Execute). If a permission is missing, it is shown as `-`.",
      "why_exists": "Enforces least-privilege permissions by defining exactly what operations are permitted for different user groups.",
      "where_used": "System files audit, SSH keys setups, application directories security integrations.",
      "real_world_example": "A private key showing `-rw-------` permissions allowing only the owner to read and write it.",
      "best_practices": "Ensure sensitive deployment keys are restricted to owner-only access to prevent leaks.",
      "common_mistakes": "Allowing global write permissions on configuration files, making them vulnerable to modifications."
    },
    {
      "title": "Numeric chmod Permissions Mapping",
      "definition": "Representing read, write, and execute permissions as octal numbers where r=4, w=2, and x=1.",
      "explanation": "Numeric notation sums permission values for each segment. Read is 4, write is 2, execute is 1. For example, `chmod 755 filename` sums owner permissions to 4+2+1=7 (rwx), group to 4+0+1=5 (rx), and others to 4+0+1=5 (rx). Standard numeric settings include 600 (owner read/write only) and 700 (owner full access, group/others locked).",
      "why_exists": "Provides an explicit, compact method to set exact file permission layouts in a single command line.",
      "where_used": "Dockerfiles creation, Terraform configurations, automation scripts.",
      "real_world_example": "Setting shell script files to `chmod 755 deploy.sh` so they can be executed by anyone but modified only by the owner.",
      "best_practices": "Use 600 for configuration configs and 700 for scripts folders to restrict traversal.",
      "common_mistakes": "Configuring public write access `chmod 777` on sensitive data paths just to quickly resolve permissions errors."
    }
  ],
  "interactive_examples": [
    {
      "objective": "Change file permissions to read and write for the owner only.",
      "command": "chmod 600 log.txt",
      "explanation": "Calculates owner as 4+2=6, group as 0, others as 0, restricting access to the owner user account.",
      "expected_output": "",
      "common_mistakes": "Forgetting the filename parameter in the command arguments.",
      "tips": "Verify the changed permissions using `ls -l log.txt` immediately after running the command."
    },
    {
      "objective": "Change the owner user of a file to root.",
      "command": "chown root log.txt",
      "explanation": "Modifies file metadata settings, setting the root account as the absolute owner.",
      "expected_output": "",
      "common_mistakes": "Attempting chown without appropriate administrative permissions, resulting in permission errors.",
      "tips": "Combine owner and group modifications in one command: `chown root:sudo log.txt`."
    }
  ],
  "lessons": [
    {
      "id": 1,
      "title": "1. Absolute Paths",
      "definition": "An absolute path defines a location starting from the root directory (/).",
      "explanation": "Absolute paths always begin with a forward slash. Example: /home/student/drafts.",
      "instruction": "Navigate to the absolute path /home/student/drafts.",
      "example": "cd /var/log/nginx",
      "expected": "/home/student/drafts",
      "hint": "Type: cd /home/student/drafts",
      "solution": "cd /home/student/drafts",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 2,
      "title": "2. Relative Paths",
      "definition": "A relative path defines a location relative to your current working directory.",
      "explanation": "Relative paths do not start with a slash. Double dots (..) represent parent directory.",
      "instruction": "Navigate to the parent directory and then into projects folder.",
      "example": "cd ../../etc",
      "expected": "/home/student/projects",
      "hint": "Type: cd ../projects",
      "solution": "cd ../projects",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 3,
      "title": "3. Permissions Overview",
      "definition": "Linux files have access modes: Read (r), Write (w), and Execute (x).",
      "explanation": "Access modes are split into: Owner (user), Group, and Others (public).",
      "instruction": "Inspect permissions of welcome.txt using detailed ls listing.",
      "example": "ls -lh welcome.txt",
      "expected": "-rw-r--r--",
      "hint": "Type: ls -l welcome.txt",
      "solution": "ls -l welcome.txt",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 4,
      "title": "4. Owner Only Access (chmod 600)",
      "definition": "chmod changes permissions settings on a file or directory.",
      "explanation": "Numeric notation: 600 gives read/write to the owner (4+2=6), and zero permissions to others.",
      "instruction": "Restrict log.txt permissions to owner read/write only.",
      "example": "chmod 600 my_private_key.pem",
      "expected": "",
      "hint": "Create log.txt if needed, then run: chmod 600 log.txt",
      "solution": "chmod 600 log.txt",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 5,
      "title": "5. Executable Scripts (chmod +x)",
      "definition": "+x adds execution permission to the target file.",
      "explanation": "Script files need execute permissions to run like programs in shell.",
      "instruction": "Make the script run.sh executable using symbolic notation.",
      "example": "chmod +x build_containers.sh",
      "expected": "",
      "hint": "Create run.sh first using touch, then type: chmod +x run.sh",
      "solution": "chmod +x run.sh",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 6,
      "title": "6. Standard Public Exec (chmod 755)",
      "definition": "755 permits owner read/write/exec, group read/exec, others read/exec.",
      "explanation": "This numeric configuration is standard for public executables and directories.",
      "instruction": "Configure permissions of run.sh explicitly to 755.",
      "example": "chmod 755 start_server.sh",
      "expected": "",
      "hint": "Type: chmod 755 run.sh",
      "solution": "chmod 755 run.sh",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 7,
      "title": "7. Directory Permissions",
      "definition": "Read on directory lists its files, write allows adding/removing files, exec allows entering.",
      "explanation": "To traverse inside folders using cd, you must have the execute flag enabled on them.",
      "instruction": "Inspect directory metadata permissions of drafts using -ld flag.",
      "example": "ls -ld /var/log/nginx",
      "expected": "drwxr-xr-x",
      "hint": "Type: ls -ld drafts",
      "solution": "ls -ld drafts",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 8,
      "title": "8. Recursive Changes (chmod -R)",
      "definition": "The -R flag recursively applies permissions to all subfolders and files.",
      "explanation": "Useful for resetting whole directories permissions at once.",
      "instruction": "Recursively grant 755 permissions to the projects directory tree.",
      "example": "chmod -R 777 /tmp/shared_assets",
      "expected": "",
      "hint": "Type: chmod -R 755 projects",
      "solution": "chmod -R 755 projects",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 9,
      "title": "9. Group Memberships",
      "definition": "Users are mapped to groups to share file permissions collectively.",
      "explanation": "The groups command outputs all group names your user is currently a member of.",
      "instruction": "Print the current active groups of your user.",
      "example": "id -Gn",
      "expected": "student sudo",
      "hint": "Type: groups",
      "solution": "groups",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 10,
      "title": "10. Check User IDs (id)",
      "definition": "The id command displays user ID (uid), group ID (gid), and group memberships.",
      "explanation": "Used to diagnose user account configurations and identity parameters.",
      "instruction": "Expose full numeric user and group IDs.",
      "example": "id -u admin",
      "expected": "uid=1000",
      "hint": "Type: id",
      "solution": "id",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 11,
      "title": "11. Changing Group Owner (chgrp)",
      "definition": "chgrp changes the group ownership of files.",
      "explanation": "Allows group members to share read/write permissions depending on group flags.",
      "instruction": "Change the group ownership of log.txt to sudo.",
      "example": "chgrp developers deploy.yaml",
      "expected": "",
      "hint": "Type: chgrp sudo log.txt",
      "solution": "chgrp sudo log.txt",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 12,
      "title": "12. Changing Owner (chown)",
      "definition": "chown reassigns the owner of a file to a new user account.",
      "explanation": "Typically requires elevated administrative/root permissions to execute.",
      "instruction": "Change owner of log.txt to root.",
      "example": "chown admin config.json",
      "expected": "",
      "hint": "Type: chown root log.txt",
      "solution": "chown root log.txt",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 13,
      "title": "13. Creation Mask (umask)",
      "definition": "umask defines the default permission bits set for newly created files.",
      "explanation": "The mask bits are subtracted from system defaults (typically 666 for files, 777 for directories).",
      "instruction": "View your system's current creation mask setting.",
      "example": "umask -S",
      "expected": "0022",
      "hint": "Type: umask",
      "solution": "umask",
      "difficulty": "Advanced",
      "estimated_duration": "3m"
    },
    {
      "id": 14,
      "title": "14. Private Folder Traverse",
      "definition": "Removing public read and execute permissions makes a folder private.",
      "explanation": "chmod 700 allows only the owner to browse and write files inside.",
      "instruction": "Restrict projects folder permissions to owner-only read/write/exec (700).",
      "example": "chmod 700 secret_folder",
      "expected": "",
      "hint": "Type: chmod 700 projects",
      "solution": "chmod 700 projects",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 15,
      "title": "15. Restrictive Delete",
      "definition": "Deleting files is allowed if the user has write access to the parent folder.",
      "explanation": "Delete the file log.txt using the rm command.",
      "instruction": "Remove log.txt permanently.",
      "example": "rm unwanted_file.txt",
      "expected": "",
      "hint": "Type: rm log.txt",
      "solution": "log.txt",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    }
  ],
  "exercises": [
    {
      "title": "Directory traverse blocks",
      "problem": "Create a directory named `private_workspace` and restrict it using chmod 700. Verify CD traversal fails if group changes.",
      "difficulty": "Intermediate",
      "hint": "Use `chmod 700 private_workspace`.",
      "expected_result": "Traversal verified locked.",
      "objective": "Understand how execute (x) flag blocks navigation."
    },
    {
      "title": "Create write-only script",
      "problem": "Modify an empty script `audit.sh` to allow owner-write only (200).",
      "difficulty": "Advanced",
      "hint": "Use `chmod 200 audit.sh`.",
      "expected_result": "File permission shows as --w-------.",
      "objective": "Master writing customized security mask configurations."
    },
    {
      "title": "Symbolic chmod changes",
      "problem": "Add user write and group execute permissions to a script using symbolic syntax.",
      "difficulty": "Beginner",
      "hint": "Use `chmod u+w,g+x script.sh`.",
      "expected_result": "Permissions modified symbolically.",
      "objective": "Learn symbol permissions formats."
    },
    {
      "title": "Audit directory ownership",
      "problem": "Identify the owner and group values of `/etc/passwd`.",
      "difficulty": "Beginner",
      "hint": "Use `ls -l /etc/passwd`.",
      "expected_result": "root root displayed in metadata column.",
      "objective": "Practice identifying active file ownership."
    },
    {
      "title": "Default Creation settings",
      "problem": "Change your active umask shell configuration to a restrictive 0077 and create a file.",
      "difficulty": "Advanced",
      "hint": "Use `umask 0077` followed by `touch new.txt`.",
      "expected_result": "new.txt created with owner-only access 600.",
      "objective": "Gain experience configuring active session creation masks."
    },
    {
      "title": "Group assignments change",
      "problem": "Reassign folder group ownership to system administration groups.",
      "difficulty": "Intermediate",
      "hint": "Use `chgrp sudo projects`.",
      "expected_result": "Group ownership modified to sudo.",
      "objective": "Practice group reassignments."
    }
  ],
  "quiz": [
    {
      "question": "Which command alters read/write/execute permissions?",
      "options": ["chown", "chgrp", "chmod", "umask"],
      "answer": "chmod",
      "explanation": "chmod (change mode) sets the permissions mask bits.",
      "incorrect_explanations": {
        "chown": "chown reassigns file user owner.",
        "chgrp": "chgrp reassigns file group owner.",
        "umask": "umask defines default masks for new creations."
      }
    },
    {
      "question": "What permissions does chmod 600 grant?",
      "options": ["Read-only for all", "Read and write for owner only", "Execute for owner only", "Full access for group members"],
      "answer": "Read and write for owner only",
      "explanation": "6 maps to 4 (read) + 2 (write) for the owner. 0 removes all access for group and others.",
      "incorrect_explanations": {
        "Read-only for all": "Represented by chmod 444.",
        "Execute for owner only": "Represented by chmod 100.",
        "Full access for group members": "Represented by chmod 070."
      }
    },
    {
      "question": "Which command is used to modify the group ownership of a file?",
      "options": ["chown", "chgrp", "chmod", "groups"],
      "answer": "chgrp",
      "explanation": "chgrp (change group) reassigns file group owners.",
      "incorrect_explanations": {
        "chown": "chown changes user ownership.",
        "chmod": "chmod alters file permission modes.",
        "groups": "groups lists active user group memberships."
      }
    },
    {
      "question": "In long format listings, what does the first character represent?",
      "options": ["Owner permissions", "File type", "Hard link count", "File size"],
      "answer": "File type",
      "explanation": "The first character indicates whether it is a directory (d), regular file (-), or link (l).",
      "incorrect_explanations": {
        "Owner permissions": "Owner permissions follow in positions 2-4.",
        "Hard link count": "Link count is shown as a number after permission characters.",
        "File size": "File size is shown after the group name."
      }
    },
    {
      "question": "How would you symbolically grant execution permission to the group?",
      "options": ["chmod g+x", "chmod o+x", "chmod u+x", "chmod a+x"],
      "answer": "chmod g+x",
      "explanation": "g refers to group, and +x adds execution rights.",
      "incorrect_explanations": {
        "chmod o+x": "Adds execution to others/world, not group.",
        "chmod u+x": "Adds execution to user/owner, not group.",
        "chmod a+x": "Adds execution to all segments."
      }
    },
    {
      "question": "What value maps to read, write, and execute permissions numerically?",
      "options": ["5", "6", "7", "4"],
      "answer": "7",
      "explanation": "Read (4) + Write (2) + Execute (1) sum up to 7.",
      "incorrect_explanations": {
        "5": "5 is read (4) + execute (1) only.",
        "6": "6 is read (4) + write (2) only.",
        "4": "4 is read only."
      }
    },
    {
      "question": "True or False: A user can enter a directory folder if they have read permissions but not execute permissions.",
      "options": ["True", "False"],
      "answer": "False",
      "explanation": "Execute permission (x) is strictly required on folders to traverse inside using cd.",
      "incorrect_explanations": {
        "True": "Without the execute flag, entering the directory fails with permission denied."
      }
    },
    {
      "question": "Which flag allows recursive permissions modifications inside a directory tree?",
      "options": ["-r", "-R", "-f", "-v"],
      "answer": "-R",
      "explanation": "The uppercase -R flag tells chmod and chown to recursively modify child files.",
      "incorrect_explanations": {
        "-r": "Lowercase -r is not the standard recursion flag for chmod.",
        "-f": "Force option to ignore error messages.",
        "-v": "Verbose logs details of changed file states."
      }
    },
    {
      "question": "What is the standard permission setting for public directories (like website folders)?",
      "options": ["777", "755", "600", "700"],
      "answer": "755",
      "explanation": "755 allows full owner access, and lets group/others read and navigate inside.",
      "incorrect_explanations": {
        "777": "Permits public writes, which is a major security risk.",
        "600": "Blocks directory navigation completely.",
        "700": "Blocks all group and public navigation."
      }
    },
    {
      "question": "Scenario: A web app script `app.py` is throwing a 'Permission Denied' execution error in your pipeline. It has `-rw-r--r--` permissions. What command fixes this?",
      "options": [
        "chmod 600 app.py",
        "chmod +x app.py",
        "chown root app.py",
        "umask 022 app.py"
      ],
      "answer": "chmod +x app.py",
      "explanation": "Adding execution (+x) permission symbolically grants the system execution rights.",
      "incorrect_explanations": {
        "chmod 600 app.py": "This removes read/exec rights for group/others and blocks execution.",
        "chown root app.py": "Changing owner does not grant execution permission bits.",
        "umask 022 app.py": "umask is a shell mask setting and cannot be run directly on a file."
      }
    }
  ],
  "resources": {
    "summary": "This module covers file structures permissions (rwx), octal representation (755, 600), changing permission states with chmod recursively, ownership modification with chown/chgrp, and umask configurations.",
    "cheat_sheet": "chmod [mode] [file] - change permissions\nchmod -R [mode] [dir] - recursive permissions\nchown [owner] [file] - change owner\nchgrp [group] [file] - change group owner\numask [mask] - change defaults creation mask",
    "commands_table": [
      {"name": "chmod", "syntax": "chmod [mode] [file]", "description": "Alters access permission bits of a file."},
      {"name": "chown", "syntax": "chown [owner] [file]", "description": "Alters user owner assignments."},
      {"name": "chgrp", "syntax": "chgrp [group] [file]", "description": "Alters group owner assignments."}
    ],
    "revision_notes": [
      "User (u) refers to owner, Group (g) to group list, Others (o) to world, All (a) to all.",
      "Octal mappings: r=4, w=2, x=1. Sum them to configure settings.",
      "Folders require execute permissions to be entered."
    ],
    "beginner_mistakes": [
      "Using chmod 777 as a generic fix for permission issues, exposing directories to public write access.",
      "Forgetting recursion flag -R when changing website subdirectories."
    ],
    "best_practices": [
      "Follow least-privilege principles by restricting configuration secrets to chmod 600.",
      "Ensure web server folders use chmod 755 or 750 for secure directory traversals."
    ],
    "interview_questions": [
      {"question": "How does Linux determine if a file is executable?", "answer": "By validating if the execution (x) bit is set on the file permissions layout."},
      {"question": "What is the difference between chmod 755 and 700?", "answer": "755 permits public reads and navigations, 700 restricts access exclusively to the owner."}
    ],
    "additional_practice": [
      "Configure a private assets directory setting chmod 700 on `/home/student/projects`.",
      "Create a read-only configurations file and test writing changes fails."
    ],
    "books": [
      {"title": "Linux Administration Handbook by Evi Nemeth", "description": "Core guide for system administrators."}
    ],
    "documentation": [
      {"title": "GNU Coreutils chmod Reference", "url": "https://www.gnu.org/software/coreutils/manual/html_node/chmod-invocation.html"}
    ],
    "external_resources": [
      {"title": "Linux Permissions Sandbox Guide", "url": "https://www.tldp.org/LDP/intro-linux/html/sect_03_04.html"}
    ]
  }
}

with open(os.path.join(base_path, "linux-file-system-permissions.json"), "w", encoding="utf-8") as f:
    json.dump(permissions_data, f, indent=2, ensure_ascii=False)
print("Enriched permissions JSON.")

# Define scripting_data
scripting_data = {
  "slug": "bash-scripting-fundamentals",
  "title": "Bash Scripting Fundamentals",
  "overview": {
    "introduction": [
      "At its core, a shell script is a simple text file containing a list of commands that the shell parses and executes sequentially. Instead of typing the same commands manually every day, DevOps engineers write Bash scripts to automate complex software builds, trigger daily database backups, clean up server disk sectors, and launch local development clusters.",
      "Bash (Bourne Again SHell) scripting is the absolute baseline programming language of infrastructure automation. When a virtual machine boots in AWS, or a container initializes inside Kubernetes, it runs boot configuration scripts written in Bash. Understanding how to use variables, loops, conditional statements, and error codes is what allows you to replace hours of manual administration work with a single automated script.",
      "This module starts from the absolute beginning: configuring your script files with the shebang syntax header, declaring and using local variables, performing numerical calculations, constructing logical checks with if-else conditionals, using loop statements to process files lists, and writing helper functions with positional parameters."
    ],
    "what_you_will_learn": [
      "The role of the shebang header line and files executable flags.",
      "Declaring shell variables and referencing scopes values.",
      "Performing numerical math calculations in the shell.",
      "Constructing logical checks and if-else branches.",
      "Writing loops (for and while) to process variables sets.",
      "Encapsulating logic blocks inside custom shell functions."
    ],
    "prerequisites": "Completion of Linux File System & Permissions course.",
    "estimated_time": "120 mins",
    "difficulty": "Intermediate",
    "learning_outcomes": [
      "Build fully automated executable scripting utilities from scratch.",
      "Incorporate variable values, conditions, and computations.",
      "Write loops that scan directories lists and perform operations.",
      "Audit exit status codes to check success flags."
    ]
  },
  "theory": [
    {
      "title": "The Shebang Syntax Header",
      "definition": "The character sequence #! at the start of a script that directs the kernel to the interpreter program.",
      "explanation": "When you execute a script using `./script.sh`, the system kernel reads the first line. The shebang `#!/bin/bash` tells the kernel that the following commands are written for the Bash shell parser and should be fed to `/bin/bash` for parsing. Without this header, the script might run using a default system shell (like Dash) which has different rules.",
      "why_exists": "Ensures consistent script execution across different Linux environments regardless of the user's default shell.",
      "where_used": "All custom system configuration scripts.",
      "real_world_example": "A script starting with `#!/bin/bash` to ensure modern bash arrays are supported.",
      "best_practices": "Always make `#!/bin/bash` the absolute first line of your custom shell scripts.",
      "common_mistakes": "Forgetting the shebang line or writing spaces before the characters, breaking execution parameters."
    },
    {
      "title": "Variables and Scope Values",
      "definition": "Named memory storage spaces used to save strings, numbers, or command execution results.",
      "explanation": "Variables are declared using standard names followed by `=` and value (e.g. `NAME='devops'`). Important: there must be absolutely no spaces around the equal sign! To reference or read the value later, prefix the variable name with the dollar symbol `$NAME`. System variables (like `$USER` or `$PATH`) are exported to make them accessible to child processes.",
      "why_exists": "Enables dynamic configuration inputs and parameter adjustments inside reusable scripts.",
      "where_used": "Environment configurations, script loops, and dynamic paths mapping.",
      "real_world_example": "Setting variables: `BACKUP_DIR='/var/backups'` and copying files using `cp -R src/ $BACKUP_DIR`.",
      "best_practices": "Use uppercase for environment variables (e.g. `PORT=80`) and lowercase for local script variables.",
      "common_mistakes": "Adding spaces around the equal sign (e.g. writing `val = 10` instead of `val=10`), throwing command errors."
    }
  ],
  "interactive_examples": [
    {
      "objective": "Perform dynamic integer math calculations.",
      "command": "echo $(( 10 + 20 ))",
      "explanation": "Evaluates math sum inside double parentheses and outputs result to standard stdout.",
      "expected_output": "30",
      "common_mistakes": "Using single parentheses which prints string brackets instead.",
      "tips": "Store calculations directly in variables: `SUM=$(( 5 + 10 ))`."
    },
    {
      "objective": "Verify if a file exists using test command conditionals.",
      "command": "[ -f welcome.txt ] && echo 'File exists'",
      "explanation": "Evaluates if welcome.txt is a regular file. If true (exit code 0), prints string using &&.",
      "expected_output": "File exists",
      "common_mistakes": "Forgetting spacing inside brackets (e.g. typing `[-f welcome.txt]` instead of `[ -f welcome.txt ]`).",
      "tips": "Spacing inside bracket tests is strictly required by the bash parser."
    }
  ],
  "lessons": [
    {
      "id": 1,
      "title": "1. Shebang & Setup",
      "definition": "The shebang (#!/bin/bash) on the first line specifies the shell interpreter.",
      "explanation": "Tells the kernel to execute the script using the bash shell runtime environment.",
      "instruction": "Create hello.sh and write shebang '#!/bin/bash' on the first line.",
      "example": "echo '#!/bin/bash' > test_script.sh",
      "expected": "",
      "hint": "Use echo '#!/bin/bash' > hello.sh",
      "solution": "echo '#!/bin/bash' > hello.sh",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 2,
      "title": "2. Script Execution",
      "definition": "Scripts are executed either with the 'bash' command or using ./ path notation.",
      "explanation": "Running 'bash script.sh' works even if the file lacks execute permissions.",
      "instruction": "Write echo 'Hello World' inside hello.sh and run it using the bash command.",
      "example": "bash run_build.sh",
      "expected": "Hello World",
      "hint": "Run: bash hello.sh",
      "solution": "bash hello.sh",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 3,
      "title": "3. Shell Variables",
      "definition": "Variables store strings, numbers, or command outputs.",
      "explanation": "Declare with name=val (no spaces!). Access using the dollar sign ($) prefix.",
      "instruction": "Export a custom environment variable named NAME set to student.",
      "example": "export ENV=production",
      "expected": "",
      "hint": "Type: export NAME=student",
      "solution": "export NAME=student",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 4,
      "title": "4. Arithmetic Operations",
      "definition": "Double parentheses (( )) evaluate arithmetic expressions in bash.",
      "explanation": "Allows basic calculations like addition, subtraction, multiplication, and divisions.",
      "instruction": "Compute the sum of 10 and 20 using double parentheses and print it.",
      "example": "echo $((5 * 5))",
      "expected": "30",
      "hint": "Type: echo $((10 + 20))",
      "solution": "echo $((10 + 20))",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 5,
      "title": "5. Numeric Comparisons",
      "definition": "Conditional flags inside [ ] compare numerical values.",
      "explanation": "-gt (greater than), -lt (less than), -eq (equals), -ne (not equals).",
      "instruction": "Test if 15 is greater than 10 using test syntax.",
      "example": "[ 50 -gt 20 ] && echo 'yes'",
      "expected": "yes",
      "hint": "Type: [ 15 -gt 10 ] && echo 'yes'",
      "solution": "[ 15 -gt 10 ] && echo 'yes'",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 6,
      "title": "6. File Check Condition",
      "definition": "The -f conditional checks if a path exists and is a regular file.",
      "explanation": "Often used in scripts to verify configurations exist before reading.",
      "instruction": "Check if welcome.txt exists using the -f test flag.",
      "example": "[ -f config.json ] && echo 'ok'",
      "expected": "found",
      "hint": "Type: [ -f welcome.txt ] && echo 'found'",
      "solution": "[ -f welcome.txt ] && echo 'found'",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 7,
      "title": "7. If Else Conditional",
      "definition": "The if statement runs different code blocks depending on truth evaluation.",
      "explanation": "Syntax: if [ test ]; then commands; else other_commands; fi",
      "instruction": "Run a conditional that creates directory logs if not already existing.",
      "example": "if [ ! -d backups ]; then mkdir backups; fi",
      "expected": "",
      "hint": "Type: if [ ! -d logs ]; then mkdir logs; fi",
      "solution": "if [ ! -d logs ]; then mkdir logs; fi",
      "difficulty": "Intermediate",
      "estimated_duration": "5m"
    },
    {
      "id": 8,
      "title": "8. Number Loops (For Range)",
      "definition": "For loops iterate a block of code over a list of items.",
      "explanation": "Ranges are represented as {1..5} to repeat actions exactly five times.",
      "instruction": "Iterate numbers 1 to 3, printing each on a new line.",
      "example": "for val in {1..10}; do echo $val; done",
      "expected": "1\n2\n3",
      "hint": "Type: for i in {1..3}; do echo $i; done",
      "solution": "for i in {1..3}; do echo $i; done",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 9,
      "title": "9. File Iterations (For Files)",
      "definition": "For loops can glob wildcards to iterate file sets dynamically.",
      "explanation": "Loops run once for each file matching the pattern (e.g., *.sh).",
      "instruction": "List all .sh files in your directory using a for loop.",
      "example": "for file in *.txt; do echo $file; done",
      "expected": "hello.sh",
      "hint": "Type: for f in *.sh; do echo $f; done",
      "solution": "hello.sh",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 10,
      "title": "10. While Loop Increment",
      "definition": "While loops execute as long as their condition evaluates to true.",
      "explanation": "Requires a condition that eventually becomes false to prevent infinite loops.",
      "instruction": "Execute a loop printing counter increments while counter is less than 3.",
      "example": "c=1; while [ $c -le 5 ]; do echo $c; c=$((c+1)); done",
      "expected": "1\n2",
      "hint": "Type: c=1; while [ $c -lt 3 ]; do echo $c; c=$((c+1)); done",
      "solution": "c=1; while [ $c -lt 3 ]; do echo $c; c=$((c+1)); done",
      "difficulty": "Intermediate",
      "estimated_duration": "5m"
    },
    {
      "id": 11,
      "title": "11. Positional Arguments",
      "definition": "$1, $2, $3... store arguments passed to the script during launch.",
      "explanation": "These allow script parameterizations. For example, ./run.sh argument1.",
      "instruction": "Print the first argument inside a temporary script call.",
      "example": "bash run.sh prod",
      "expected": "verified",
      "hint": "Create script writing 'echo $1' then run: bash arg.sh verified",
      "solution": "bash arg.sh verified",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 12,
      "title": "12. Interactive Read Input",
      "definition": "The read command pauses script execution to capture keyboard inputs.",
      "explanation": "Prompts user input, storing the response inside a named variable.",
      "instruction": "Read user input into var and echo back. (Use simulation to check commands)",
      "example": "echo 'syntax example'",
      "expected": "verified",
      "hint": "Type: echo 'verified'",
      "solution": "echo 'verified'",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 13,
      "title": "13. Exit Status Code ($?)",
      "definition": "Every Linux command returns an exit status code between 0 and 255.",
      "explanation": "0 means success. Any non-zero code represents an error code.",
      "instruction": "Check the exit status of the previous command using echo $?.",
      "example": "ping -c 1 google.com; echo $?",
      "expected": "0",
      "hint": "Type: echo $?",
      "solution": "echo $?",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 14,
      "title": "14. Custom Functions",
      "definition": "Functions bundle reusable command steps in shell scripts.",
      "explanation": "Declare using function_name() { ... } structure and call by name.",
      "instruction": "Invoke a function named greet that prints hello.",
      "example": "hello() { echo 'hi'; }; hello",
      "expected": "hello",
      "hint": "Type: greet() { echo 'hello'; }; greet",
      "solution": "greet() { echo 'hello'; }; greet",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 15,
      "title": "15. Local Variable Scope",
      "definition": "The local keyword restricts a variable's visibility to its function.",
      "explanation": "Prevents accidental side effects and name collisions in scripts.",
      "instruction": "Run a function containing a local variable mapping to local_val.",
      "example": "test() { local var='val'; echo $var; }; test",
      "expected": "local_val",
      "hint": "Type: func() { local val='local_val'; echo $val; }; func",
      "solution": "func() { local val='local_val'; echo $val; }; func",
      "difficulty": "Advanced",
      "estimated_duration": "4m"
    }
  ],
  "exercises": [
    {
      "title": "Automation directory backup",
      "problem": "Create a script `backup_run.sh` that checks if directory `data` exists, and if so, copies all contents to a `backup` folder.",
      "difficulty": "Intermediate",
      "hint": "Use `if [ -d data ]; then cp -R data/ backup/; fi`.",
      "expected_result": "Script correctly copies folder data files.",
      "objective": "Practice implementing logical path checks."
    },
    {
      "title": "Math increment values",
      "problem": "Write a script that reads numerical value inputs and increments them using a double parentheses construct.",
      "difficulty": "Beginner",
      "hint": "Declare `c=5` followed by `echo $((c + 1))`.",
      "expected_result": "Outputs the calculation value result.",
      "objective": "Practice arithmetic variables logic."
    },
    {
      "title": "For loop directories listing",
      "problem": "Create a loop iterating through files ending in `.sh` and print their filenames to terminal output.",
      "difficulty": "Intermediate",
      "hint": "Use `for f in *.sh; do echo $f; done`.",
      "expected_result": "Prints all script names present.",
      "objective": "Practice directory globbing loops."
    },
    {
      "title": "Positional inputs configurations",
      "problem": "Construct a deployment script `setup.sh` that checks if the first parameter is 'production' and logs messages.",
      "difficulty": "Intermediate",
      "hint": "Evaluate `if [ \"$1\" = \"production\" ]; then echo 'Deploying...'; fi`.",
      "expected_result": "Prints deployment messages if matching parameter is passed.",
      "objective": "Learn using positional arguments inside conditions."
    },
    {
      "title": "Custom logs rotator function",
      "problem": "Write a local function `clean_logs()` that empties a temporary file and returns an exit code.",
      "difficulty": "Advanced",
      "hint": "Declare `clean_logs() { echo '' > temp.log; return 0; }`.",
      "expected_result": "Function runs successfully resetting log content.",
      "objective": "Practice encapsulation using shell functions."
    },
    {
      "title": "While loop delay counter",
      "problem": "Write a loop utility that prints countdown integers from 3 to 1.",
      "difficulty": "Advanced",
      "hint": "Use `c=3; while [ $c -gt 0 ]; do echo $c; c=$((c - 1)); done`.",
      "expected_result": "Prints 3, 2, 1 sequentially.",
      "objective": "Gain experience writing conditional loops."
    }
  ],
  "quiz": [
    {
      "question": "Which character combination is known as the shebang and directs the script to the proper shell interpreter?",
      "options": ["##", "/*", "#!", "$!"],
      "answer": "#!",
      "explanation": "#! points the kernel loader to the program executable parser path (e.g. /bin/bash).",
      "incorrect_explanations": {
        "##": "Double hash represents string comments.",
        "/*": "Forward slash star represents block comments in languages like C.",
        "$!": "Special variable returning PID of last background process."
      }
    },
    {
      "question": "Which variable declaration is valid in a Bash shell environment?",
      "options": ["NAME = student", "NAME=student", "NAME:student", "$NAME=student"],
      "answer": "NAME=student",
      "explanation": "Bash requires name=value syntax with absolutely no spaces around the equal sign.",
      "incorrect_explanations": {
        "NAME = student": "Fails because the parser interprets 'NAME' as a command and '=' as an argument.",
        "NAME:student": "Colon is not the variables assignment operator in bash.",
        "$NAME=student": "Dollar prefix reads values, it cannot define new variables assignments."
      }
    },
    {
      "question": "How do you evaluate arithmetic math calculations inside a script?",
      "options": ["$(( expr ))", "$[ expr ]", "[ expr ]", "expr"],
      "answer": "$(( expr ))",
      "explanation": "Double parentheses with dollar symbol prefix are the standard syntax for integer arithmetic expansions.",
      "incorrect_explanations": {
        "$[ expr ]": "Deprecated syntax for numeric evaluations, no longer recommended.",
        "[ expr ]": "Brackets evaluate conditional string/logical tests, not mathematical operations.",
        "expr": "Evaluates as a raw text string unless run through backticks."
      }
    },
    {
      "question": "Which comparison flag is used to check if a numeric value is 'greater than' another?",
      "options": ["-eq", "-ne", "-gt", "-lt"],
      "answer": "-gt",
      "explanation": "-gt stands for 'greater than' and is used inside logical tests [ ].",
      "incorrect_explanations": {
        "-eq": "Stands for 'equals'.",
        "-ne": "Stands for 'not equal to'.",
        "-lt": "Stands for 'less than'."
      }
    },
    {
      "question": "What is the role of the -f check flag inside bracket test evaluations?",
      "options": ["Checks if path is a directory", "Checks if file is executable", "Checks if path is a regular file", "Forces file overrides"],
      "answer": "Checks if path is a regular file",
      "explanation": "-f returns true (exit 0) if the target path points to a valid regular file.",
      "incorrect_explanations": {
        "Checks if path is a directory": "Evaluated using the -d directory flag.",
        "Checks if file is executable": "Evaluated using the -x permission flag.",
        "Forces file overrides": "-f does not change file access permissions."
      }
    },
    {
      "question": "How do you correctly close an if conditional block in Bash?",
      "options": ["endif", "fi", "done", "close"],
      "answer": "fi",
      "explanation": "fi is 'if' written backward, indicating the end of the conditional logic sequence.",
      "incorrect_explanations": {
        "endif": "Used in other programming languages or C-Shell, not Bash.",
        "done": "Used to terminate loop constructs (for/while).",
        "close": "Not a keyword terminator in bash programming."
      }
    },
    {
      "question": "Which Special Variable holds the exit status code of the last executed command?",
      "options": ["$#", "$@", "$?", "$!"],
      "answer": "$?",
      "explanation": "$? holds status (0 for success, non-zero representing system error code).",
      "incorrect_explanations": {
        "$#": "Holds the count of positional parameters passed to a script.",
        "$@": "Represents the array list of all parameters.",
        "$!": "Holds the PID of the last background job process."
      }
    },
    {
      "question": "True or False: Spacing inside bracket logical tests (e.g. `[ $A -gt $B ]`) is completely optional.",
      "options": ["True", "False"],
      "answer": "False",
      "explanation": "Brackets are aliases to the test command utility; they strictly require space margins to parse parameters.",
      "incorrect_explanations": {
        "True": "Omitting space (e.g. `[$A -gt $B]`) causes syntax errors."
      }
    },
    {
      "question": "What does the local keyword do when declared before variables inside a function?",
      "options": ["Makes them system-wide variables", "Restricts variable scope strictly to the function", "Speeds up mathematical evaluations", "Locks files permission settings"],
      "answer": "Restricts variable scope strictly to the function",
      "explanation": "local prevents the variable from leaking out or colliding with global variables in parent scopes.",
      "incorrect_explanations": {
        "Makes them system-wide variables": "This is done using the export command.",
        "Speeds up mathematical evaluations": "Has no effect on calculation runtime speeds.",
        "Locks files permission settings": "Does not relate to directory security permissions."
      }
    },
    {
      "question": "Scenario: You need a script loop that runs exactly 5 times printing counter loops. Which construct is best?",
      "options": [
        "for i in {1..5}; do echo $i; done",
        "while [ i -eq 5 ]; do echo $i; done",
        "if [ $i -lt 5 ]; then echo $i; fi",
        "for i in *.sh; do echo $i; done"
      ],
      "answer": "for i in {1..5}; do echo $i; done",
      "explanation": "The range indicator {1..5} runs the block exactly five times, outputting the index each step.",
      "incorrect_explanations": {
        "while [ i -eq 5 ]; do echo $i; done": "Would trigger syntax errors since i is not initialized, or loop infinitely if i is 5.",
        "if [ $i -lt 5 ]; then echo $i; fi": "This is a conditional statement that evaluates once, not a loop structure.",
        "for i in *.sh; do echo $i; done": "Loops over files ending in .sh, which depends on folder contents, not a fixed range."
      }
    }
  ],
  "resources": {
    "summary": "This module covers shebang shell script headers, variables mapping, arithmetic operations, bracket comparisons, conditional blocks, loops, exit status checks, and function wrappers.",
    "cheat_sheet": "#!/bin/bash - shebang line\nNAME=val - set variable\n$NAME - read variable\n$((A+B)) - sum math\n[ -f file ] - check file\nif [ cond ]; then ...; fi - conditional\nfor i in list; do ...; done - loop\n$? - exit code\nfunc() { ... } - custom function",
    "commands_table": [
      {"name": "read", "syntax": "read [varname]", "description": "Pause execution capturing keyboard standard input values."},
      {"name": "export", "syntax": "export [name=val]", "description": "Promotes local variables to environment scope variables."}
    ],
    "revision_notes": [
      "Spacing inside brackets is strictly mandatory: `[ $x -eq 1 ]`.",
      "Variables set with NAME=val, no spaces around the equal sign.",
      "Use exit status $? directly to check errors after executing system utilities."
    ],
    "beginner_mistakes": [
      "Writing script logic without setting files executable permissions (+x), prompting permission denied errors on launch.",
      "Adding spaces around equals during variable declaration: `var = val`."
    ],
    "best_practices": [
      "Always declare variables scopes local inside helper shell functions.",
      "Double quote variables representing file paths to prevent space splitting errors."
    ],
    "interview_questions": [
      {"question": "How do you pass arguments to a script?", "answer": "By passing parameters space-separated after the script command: `./script.sh arg1 arg2`."},
      {"question": "What is the difference between > and >>?", "answer": "> overwrites target files contents; >> appends new data lines to the bottom of the files."}
    ],
    "additional_practice": [
      "Write an automated deployment utility archiving log files into backups folders.",
      "Construct a shell configuration script dynamically writing env variables into a config profile."
    ],
    "books": [
      {"title": "Classic Shell Scripting by Arnold Robbins", "description": "The definitive textbook for automated operations scripts."}
    ],
    "documentation": [
      {"title": "GNU Bash Reference Manual", "url": "https://www.gnu.org/software/bash/manual/"}
    ],
    "external_resources": [
      {"title": "Bash Hackers Wiki", "url": "https://wiki.bash-hackers.org/"}
    ]
  }
}

with open(os.path.join(base_path, "bash-scripting-fundamentals.json"), "w", encoding="utf-8") as f:
    json.dump(scripting_data, f, indent=2, ensure_ascii=False)
print("Enriched scripting JSON.")

# Define networking_data
networking_data = {
  "slug": "linux-networking-processes",
  "title": "Linux Networking & Processes",
  "overview": {
    "introduction": [
      "An operating system is a busy hive of activity, with hundreds of programs running simultaneously in the background. In Linux, these running programs are called 'processes'. To manage a system effectively, DevOps engineers must be able to monitor CPU/memory usage, background or suspend tasks, and terminate processes that are frozen or consuming too many resources.",
      "Furthermore, modern applications do not run in isolation. They communicate over networks, bind to TCP/UDP ports, listen for HTTP requests, and resolve domains using DNS. Whether you are deploying a microservice in Docker or debugging connection failures between a web app and a database, you must know how to inspect network interfaces, check open ports, audit active sockets, and verify connectivity parameters.",
      "This module bridges processes management and networks configurations: managing processes using ps, top, and kill; utilizing jobs background controls; checking networking adapter bindings using ip address; auditing listening ports using ss; resolving DNS lookups via dig; and monitoring services status using systemctl."
    ],
    "what_you_will_learn": [
      "Monitoring system processes utilizing ps and top metrics tables.",
      "Spawning background processes and managing jobs control with fg and jobs.",
      "Terminating unresponsive threads using kill signals.",
      "Inspecting local network cards interfaces and gateway routes.",
      "Auditing TCP server listening socket ports using ss.",
      "Testing server connections and domain routing via ping, curl, and dig."
    ],
    "prerequisites": "Completion of Bash Scripting Fundamentals course.",
    "estimated_time": "100 mins",
    "difficulty": "Advanced",
    "learning_outcomes": [
      "Monitor, stop, background, and foreground system tasks safely.",
      "Diagnose local networks configuration adapter details and route tables.",
      "Identify socket leaks and map listening ports to PIDs.",
      "Verify DNS record registrations and retrieve headers via cURL."
    ]
  },
  "theory": [
    {
      "title": "Process States and Lifecycle Controllers",
      "definition": "Active program processes identified by a Process ID (PID) that traverse running, sleeping, or stopped states.",
      "explanation": "Every program runs inside a process scope. The kernel assigns a unique PID. You list active terminal processes with `ps`, or the whole system via `ps aux`. To stop a process, send a signal using `kill [PID]`. SIGTERM (15) asks nicely to shut down; SIGKILL (9) forces immediate termination by the kernel.",
      "why_exists": "Allows safe monitoring, allocation of CPU resources, and cleaning of orphan processes.",
      "where_used": "Sysadmin checks, system automation monitoring scripts, containers health audits.",
      "real_world_example": "Finding a stuck web server process using `ps aux | grep nginx` and terminating it using `kill -9 1245`.",
      "best_practices": "Always try termination signal 15 (SIGTERM) first to allow processes to close connection pools safely before resorting to signal 9.",
      "common_mistakes": "Forgetting that process PIDs are dynamic, and accidentally running kill on incorrect IDs."
    },
    {
      "title": "Active Ports and Socket Audits",
      "definition": "Network sockets bound to port numbers, allowing communication between processes across network interfaces.",
      "explanation": "Applications bind to sockets (IP + Port) to listen for connections. The `ss` utility scans sockets, replacing the older `netstat` tool. Running `ss -lnt` lists all TCP listening sockets. If a database binds to port 5432, you will see `*:5432` in the listing. You can map socket bounds to PIDs using the `-p` flag.",
      "why_exists": "Diagnoses port conflicts (e.g. two web servers trying to bind to port 80) and detects open ports that pose security risks.",
      "where_used": "Nginx config audits, firewalls configurations, microservices debugs.",
      "real_world_example": "Confirming PostgreSQL server is running and listening on all network interfaces via port 5432.",
      "best_practices": "Verify applications only listen on loopback interface `127.0.0.1` if they do not need to accept public external connections.",
      "common_mistakes": "Trying to start a container service and getting 'address already in use' errors without auditing existing socket bounds."
    }
  ],
  "interactive_examples": [
    {
      "objective": "Spawning processes in the background.",
      "command": "sleep 100 &",
      "explanation": "Executes the sleep utility in the background, returning a job ID [1] and PID. Keeps the prompt active.",
      "expected_output": "[1] 12405",
      "common_mistakes": "Forgetting the space before the ampersand symbol.",
      "tips": "Inspect background tasks anytime using the `jobs` command."
    },
    {
      "objective": "Audit active listening TCP ports.",
      "command": "ss -lnt",
      "explanation": "Queries the kernel socket state table, listing TCP ports currently listening for connections.",
      "expected_output": "LISTEN 0 128 *:80 *:*",
      "common_mistakes": "Typing uppercase flags instead of lowercase -lnt.",
      "tips": "Pass -p flag (requires root permissions) to output the PID of the process bound to the port."
    }
  ],
  "lessons": [
    {
      "id": 1,
      "title": "1. Terminal Processes (ps)",
      "definition": "Processes are active running instances of programs in Linux.",
      "explanation": "The ps command lists processes running in your current terminal session.",
      "instruction": "Print the processes running in this terminal session.",
      "example": "ps -e",
      "expected": "ps",
      "hint": "Type: ps",
      "solution": "ps",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 2,
      "title": "2. System Processes (ps aux)",
      "definition": "ps aux prints all running processes across the whole system.",
      "explanation": "a (all users), u (detailed fields), x (processes not attached to terminals).",
      "instruction": "Expose details of all running processes in the system.",
      "example": "ps -ef",
      "expected": "PID TTY",
      "hint": "Type: ps aux",
      "solution": "ps aux",
      "difficulty": "Beginner",
      "estimated_duration": "4m"
    },
    {
      "id": 3,
      "title": "3. Real-time Monitoring (top)",
      "definition": "top displays a real-time, dynamic view of active running processes.",
      "explanation": "Outputs CPU cycles, RAM consumptions, uptime details, and active threads.",
      "instruction": "Query process dynamic parameters using top.",
      "example": "htop",
      "expected": "htop",
      "hint": "Type: top",
      "solution": "top",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 4,
      "title": "4. Terminate Processes (kill)",
      "definition": "The kill command sends signals to terminate running processes.",
      "explanation": "Requires a target Process ID (PID). SIGKILL (-9) forces immediate shutdown.",
      "instruction": "Terminate a process with PID 9999 (use simulation standard return).",
      "example": "kill 1234",
      "expected": "",
      "hint": "Type: kill 9999",
      "solution": "kill 9999",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 5,
      "title": "5. Background Jobs (sleep &)",
      "definition": "The ampersand (&) executes a command in the background.",
      "explanation": "Keeps the terminal responsive for more commands while it executes.",
      "instruction": "Run a sleep command for 100 seconds in the background.",
      "example": "sleep 600 &",
      "expected": "[1]",
      "hint": "Type: sleep 100 &",
      "solution": "sleep 100 &",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 6,
      "title": "6. Job Controller (jobs)",
      "definition": "The jobs command lists background processes spawned by this shell.",
      "explanation": "Shows status (running, stopped) and job number identifiers.",
      "instruction": "Expose current background job listings.",
      "example": "jobs -l",
      "expected": "Running",
      "hint": "Type: jobs",
      "solution": "jobs",
      "difficulty": "Intermediate",
      "estimated_duration": "3m"
    },
    {
      "id": 7,
      "title": "7. Bring to Foreground (fg)",
      "definition": "fg moves background jobs to the foreground, letting them take terminal focus.",
      "explanation": "Takes a job identifier parameter, for example, fg %1.",
      "instruction": "Bring background job 1 back to the foreground.",
      "example": "fg %2",
      "expected": "sleep 100",
      "hint": "Type: fg %1",
      "solution": "fg %1",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 8,
      "title": "8. Network Interfaces (ip a)",
      "definition": "ip address (ip a) displays local network adapters and IP configurations.",
      "explanation": "Used to verify local adapter status, loopbacks, and network parameters.",
      "instruction": "List all network card configurations.",
      "example": "ifconfig",
      "expected": "eth0",
      "hint": "Type: ip a",
      "solution": "ip a",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 9,
      "title": "9. Gateway Routes (ip route)",
      "definition": "ip route outputs network routing lookup tables.",
      "explanation": "Exposes destination gateways, interfaces, and gateway routing parameters.",
      "instruction": "View active network routing tables.",
      "example": "route -n",
      "expected": "default via",
      "hint": "Type: ip route",
      "solution": "ip route",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 10,
      "title": "10. Connectivity Ping",
      "definition": "ping sends ICMP ECHO_REQUEST packets to verify connection status.",
      "explanation": "Validates if a remote host is alive and responding.",
      "instruction": "Ping google.com to verify connectivity.",
      "example": "ping -c 3 yahoo.com",
      "expected": "64 bytes from",
      "hint": "Type: ping google.com",
      "solution": "ping google.com",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 11,
      "title": "11. Active Sockets (ss)",
      "definition": "ss dumps socket statistics, replacing the older netstat tool.",
      "explanation": "Shows active listening TCP/UDP ports, matching connection routes.",
      "instruction": "Display active TCP socket listings.",
      "example": "netstat -plnt",
      "expected": "State",
      "hint": "Type: ss",
      "solution": "ss",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 12,
      "title": "12. DNS Lookup (dig)",
      "definition": "dig performs DNS record resolution lookups.",
      "explanation": "Queries name servers for A, MX, CNAME, and TXT mapping parameters.",
      "instruction": "Query DNS record details for google.com.",
      "example": "nslookup yahoo.com",
      "expected": "ANSWER SECTION",
      "hint": "Type: dig google.com",
      "solution": "dig google.com",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 13,
      "title": "13. HTTP Requests (curl)",
      "definition": "curl transfers data from or to a server using supported protocols.",
      "explanation": "Commonly used to test API services or download configurations.",
      "instruction": "Fetch headers from an endpoint using curl.",
      "example": "wget --spider https://www.google.com",
      "expected": "HTTP/1.1 200 OK",
      "hint": "Type: curl -I https://www.google.com",
      "solution": "curl -I https://www.google.com",
      "difficulty": "Beginner",
      "estimated_duration": "3m"
    },
    {
      "id": 14,
      "title": "14. Systemd Services",
      "definition": "systemctl manages systemd services status and boot processes.",
      "explanation": "Can inspect, launch, reload, disable, or stop daemon services.",
      "instruction": "Check the status of the nginx service.",
      "example": "service apache2 status",
      "expected": "Active: active (running)",
      "hint": "Type: systemctl status nginx",
      "solution": "systemctl status nginx",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    },
    {
      "id": 15,
      "title": "15. Restarting Daemons",
      "definition": "systemctl restart stops and immediately starts a system service.",
      "explanation": "Commonly executed after updating configuration files to reload parameters.",
      "instruction": "Restart the nginx service to reload configurations.",
      "example": "service apache2 restart",
      "expected": "",
      "hint": "Type: systemctl restart nginx",
      "solution": "systemctl restart nginx",
      "difficulty": "Intermediate",
      "estimated_duration": "4m"
    }
  ],
  "exercises": [
    {
      "title": "Background daemon checks",
      "problem": "Spawn a long-sleeping background process, find its PID using ps, and kill it with SIGKILL.",
      "difficulty": "Intermediate",
      "hint": "Run `sleep 999 &` followed by `ps aux | grep sleep` then `kill -9 [PID]`.",
      "expected_result": "Process terminated by kernel.",
      "objective": "Practice background execution and target kill workflows."
    },
    {
      "title": "Gateway interfaces audits",
      "problem": "Identify your active gateway route interfaces mapping.",
      "difficulty": "Beginner",
      "hint": "Use `ip route`.",
      "expected_result": "Outputs the default route interface info.",
      "objective": "Understand routing table mappings."
    },
    {
      "title": "Audit Nginx ports",
      "problem": "Verify if the local web server is listening on port 80.",
      "difficulty": "Intermediate",
      "hint": "Use `ss -lnt` or `netstat -an`.",
      "expected_result": "LISTEN entry shown for port 80.",
      "objective": "Practice auditing socket port listings."
    },
    {
      "title": "DNS records trace",
      "problem": "Resolve domain names IP registers for a custom nameserver.",
      "difficulty": "Advanced",
      "hint": "Use `dig google.com` or `nslookup google.com`.",
      "expected_result": "DNS answer section lists IP mapping details.",
      "objective": "Learn DNS troubleshooting techniques."
    },
    {
      "title": "Curl API testing",
      "problem": "Test Nginx server configuration by fetching raw page headers.",
      "difficulty": "Beginner",
      "hint": "Use `curl -I http://localhost`.",
      "expected_result": "Nginx server header information displayed.",
      "objective": "Gain experience testing application connectivity."
    },
    {
      "title": "Auto service reload",
      "problem": "Inspect the nginx systemd configuration files status and perform restarts.",
      "difficulty": "Advanced",
      "hint": "Use `systemctl status nginx` followed by `systemctl restart nginx`.",
      "expected_result": "Service restarted successfully.",
      "objective": "Learn system daemon management concepts."
    }
  ],
  "quiz": [
    {
      "question": "Which command lists running processes in your current terminal session?",
      "options": ["jobs", "ps", "top", "ss"],
      "answer": "ps",
      "explanation": "ps displays process snapshots attached to your active TTY screen.",
      "incorrect_explanations": {
        "jobs": "Lists shell background tasks only, not all session threads.",
        "top": "Provides real-time dynamic monitor dashboard.",
        "ss": "Displays network socket connections, not active system processes."
      }
    },
    {
      "question": "What is the process ID (PID) of the first process initialized by the Linux kernel (init/systemd)?",
      "options": ["0", "1", "100", "10"],
      "answer": "1",
      "explanation": "PID 1 is reserved for the initial system systemd/init task, parent of all other threads.",
      "incorrect_explanations": {
        "0": "PID 0 is reserved for scheduler/swapper, not a standard system task.",
        "100": "PID 100 is assigned to standard children daemons.",
        "10": "PID 10 holds system processes."
      }
    },
    {
      "question": "Which signal number is sent by kill -9 to force termination?",
      "options": ["SIGTERM (15)", "SIGKILL (9)", "SIGINT (2)", "SIGHUP (1)"],
      "answer": "SIGKILL (9)",
      "explanation": "Signal 9 tells the Linux kernel to immediately stop the process, bypassing normal cleanup.",
      "incorrect_explanations": {
        "SIGTERM (15)": "Signal 15 requests graceful termination, allowing state saving.",
        "SIGINT (2)": "Interrupt signal sent by Ctrl+C in terminal sessions.",
        "SIGHUP (1)": "Hangup signal typically used to reload configurations."
      }
    },
    {
      "question": "How do you run a command in the background from your shell?",
      "options": ["Append &", "Prefix bg", "Append %", "Prefix systemctl"],
      "answer": "Append &",
      "explanation": "Appending an ampersand & executes the program as a background job task.",
      "incorrect_explanations": {
        "Prefix bg": "bg is a separate command that resumes stopped jobs in the background.",
        "Append %": "% references job IDs inside foreground/kill commands.",
        "Prefix systemctl": "systemctl manages daemon services, it does not launch random CLI tasks in background."
      }
    },
    {
      "question": "Which utility checks IP address configurations of local network interfaces?",
      "options": ["ip a", "ss", "dig", "top"],
      "answer": "ip a",
      "explanation": "ip address (abbreviated ip a) prints local interface adapters, configurations, and network states.",
      "incorrect_explanations": {
        "ss": "ss queries network sockets, not adapter hardware configurations.",
        "dig": "dig performs external DNS routing queries.",
        "top": "top monitors process resources."
      }
    },
    {
      "question": "Which command checks TCP server listening sockets?",
      "options": ["ip route", "top", "ss -lnt", "ping"],
      "answer": "ss -lnt",
      "explanation": "ss with -l (listening) and -n (numeric) outputs TCP ports active on the machine.",
      "incorrect_explanations": {
        "ip route": "Displays gateway routing information.",
        "top": "Monitors CPU and memory statistics.",
        "ping": "Tests ICMP connectivity, does not show ports."
      }
    },
    {
      "question": "True or False: The ping utility validates if a specific port (like 80) is listening on a server.",
      "options": ["True", "False"],
      "answer": "False",
      "explanation": "ping utilizes ICMP packets that verify machine connectivity, not specific socket ports.",
      "incorrect_explanations": {
        "True": "To test specific ports, use curl, telnet, or netcat instead."
      }
    },
    {
      "question": "Which DNS query tool returns A record registrations?",
      "options": ["ip route", "dig", "curl", "ss"],
      "answer": "dig",
      "explanation": "dig (domain information groper) resolves DNS mappings and returns domain details.",
      "incorrect_explanations": {
        "ip route": "Exposes gateway routes.",
        "curl": "Downloads HTTP pages contents.",
        "ss": "Lists socket states."
      }
    },
    {
      "question": "Which systemctl command stops and immediately starts a service?",
      "options": ["reload", "restart", "start", "enable"],
      "answer": "restart",
      "explanation": "restart performs a stop action followed by a start action, resetting process parameters.",
      "incorrect_explanations": {
        "reload": "Asks the service process to re-read configs without stopping the main process.",
        "start": "Launches a stopped service, has no effect if running.",
        "enable": "Configures the service to launch automatically during system boots."
      }
    },
    {
      "question": "Scenario: A web app client is failing to connect to your service. You want to verify Nginx is actively listening. What command do you run?",
      "options": [
        "ip route",
        "ss -lntp",
        "systemctl enable nginx",
        "dig localhost"
      ],
      "answer": "ss -lntp",
      "explanation": "ss -lntp checks all listening ports along with the process IDs and names associated with each socket.",
      "incorrect_explanations": {
        "ip route": "Checks gateway routing configurations.",
        "systemctl enable nginx": "Enables boot start but does not report active port details.",
        "dig localhost": "Performs DNS lookup on localhost, which does not check port bindings."
      }
    }
  ],
  "resources": {
    "summary": "This module reviews processes lifecycle controls ps, top, kill, jobs foregrounding, network adapters configuration ip, gateway routes, active socket ports audits ss, and systemd services scripts systemctl.",
    "cheat_sheet": "ps aux - show all processes\ntop - real-time monitor\nkill -9 [PID] - force kill\nsleep 10 & - start background job\njobs - list background jobs\nfg %[id] - foreground job\nip a - show network cards\nss -lntp - show open ports\ndig [domain] - DNS lookup\ncurl -I [url] - fetch web headers\nsystemctl restart [service] - restart daemon",
    "commands_table": [
      {"name": "ps", "syntax": "ps aux", "description": "Displays detailed processes snapshot listing."},
      {"name": "kill", "syntax": "kill -[signal] [PID]", "description": "Sends signal code to target PID context."},
      {"name": "ss", "syntax": "ss -lntp", "description": "Audits active TCP/UDP ports bounds."}
    ],
    "revision_notes": [
      "Process signal 15 (SIGTERM) allows graceful shutdown, signal 9 (SIGKILL) forces termination.",
      "Use `ss -lntp` as root to map listening ports to active program names.",
      "DNS lookups utilize the local resolver configs configured at `/etc/resolv.conf`."
    ],
    "beginner_mistakes": [
      "Killing correct program PIDs using incorrect signal contexts.",
      "Confusing `systemctl enable` (run on startup boot) with `systemctl start` (runs service immediately)."
    ],
    "best_practices": [
      "Background long-running migration scripts using `nohup` or screen/tmux environments.",
      "Verify port availability with `ss` before setting host port configs."
    ],
    "interview_questions": [
      {"question": "How do you check memory metrics in real-time?", "answer": "Use top, htop, or free -m commands."},
      {"question": "What does a LISTEN state represent on port 80?", "answer": "It indicates a web server is bound and ready to accept web connections."}
    ],
    "additional_practice": [
      "Spawn a background script logging to file and inspect it using top.",
      "Verify local HTTP configuration response code using cURL."
    ],
    "books": [
      {"title": "UNIX and Linux System Administration Handbook", "description": "The golden standard guide for Linux systems management."}
    ],
    "documentation": [
      {"title": "systemd System and Service Manager Documentation", "url": "https://www.freedesktop.org/wiki/Software/systemd/"}
    ],
    "external_resources": [
      {"title": "Linux Processes and Networking Guide", "url": "https://www.digitalocean.com/community/tutorial_series/getting-started-with-linux"}
    ]
  }
}

with open(os.path.join(base_path, "linux-networking-processes.json"), "w", encoding="utf-8") as f:
    json.dump(networking_data, f, indent=2, ensure_ascii=False)
print("Enriched networking JSON.")

# Define capstone_data
capstone_data = {
  "slug": "linux-capstone-project",
  "title": "Linux Capstone Project",
  "overview": {
    "introduction": [
      "In this final Capstone Project, you will step into the shoes of a DevOps Engineer tasked with deploying and securing a production environment. You will pull together all the individual concepts from the previous modules: navigating the directory tree, configuring restrictive permissions, writing automated bash utility scripts, managing system service accounts, and auditing active network sockets.",
      "This is not a theoretical exercise. You will build a simulated deployment workflow: creating the workspace structure under a dedicated path, writing server configurations, automating log rotations, running script services in the background, redirecting outputs, and verifying port bounds.",
      "This module serves as the final integration benchmark. Success in this module demonstrates that you are ready to transition to container orchestrations with Docker, cloud infrastructure with Terraform, and Kubernetes cluster deployments."
    ],
    "what_you_will_learn": [
      "Creating nested application workspaces structure.",
      "Configuring secure permission profiles on server settings.",
      "Writing log rotation backup scripts.",
      "Managing system administration permissions boundaries.",
      "Deploying application scripts in background daemon mode.",
      "Auditing TCP sockets and active system jobs listings."
    ],
    "prerequisites": "Completion of Linux Networking & Processes course.",
    "estimated_time": "120 mins",
    "difficulty": "Advanced",
    "learning_outcomes": [
      "Deploy a complete, secured application framework in Linux.",
      "Enforce least-privilege permissions boundaries across files and processes.",
      "Create automated scripts that rotate and clear log files.",
      "Audit active ports and verify background daemon execution status."
    ]
  },
  "theory": [
    {
      "title": "Production Deployment Workspace Architectures",
      "definition": "Structuring folders and service accounts according to the principle of least privilege.",
      "explanation": "A standard application deployment has separate directories for source code (`src`), configurations (`configs`), and backup logs (`backups`). Placing these inside a single parent structure makes path mappings clean. Assigning the whole tree to a restricted service user account prevents regular users from modifying configurations settings.",
      "why_exists": "Minimizes blast radius; if the web server is compromised, the attacker cannot read files outside the designated folders.",
      "where_used": "Cloud server deployments, container templates config, platform integrations.",
      "real_world_example": "Setting application directories to `/var/www/my-app` owned by user `www-data`.",
      "best_practices": "Ensure backup directories are read-only for standard application processes to prevent modifications of history log logs.",
      "common_mistakes": "Running production deployment workflows directly using the root account, exposing the whole server to risks."
    },
    {
      "title": "Automation Log Rotators",
      "definition": "A script or daemon utility that truncates or archives active log files to prevent storage depletion.",
      "explanation": "If a server process writes logs indefinitely, it will eventually consume 100% of the disk, crash the database, and freeze the system. A log rotator script periodically backs up the active logs, clears the file (truncation), and stores history compressions. Truncating a file can be done by echoing an empty string: `echo '' > app.log`.",
      "why_exists": "Guarantees continuous system uptime by keeping disk space consumption within bounded boundaries.",
      "where_used": "Sysadmin cron automation schedules, container logs configurations.",
      "real_world_example": "A logrotate cron job clearing `/var/log/nginx/access.log` daily.",
      "best_practices": "Always archive active logs to a separate backup drive before truncating.",
      "common_mistakes": "Deleting active log files (which breaks the process holding the descriptor) instead of truncating them."
    }
  ],
  "interactive_examples": [
    {
      "objective": "Recursively assign directory ownership to a service user account.",
      "command": "chown -R devops_admin capstone",
      "explanation": "Sets devops_admin as the owner of capstone and all its child files recursively.",
      "expected_output": "",
      "common_mistakes": "Forgetting the uppercase recursion flag -R.",
      "tips": "Always run ls -la to check if the owner column shows the new service user name."
    },
    {
      "objective": "Launch a process in the background and redirect output to a log.",
      "command": "bash app.sh > app.log &",
      "explanation": "Spawns the app.sh script in the background, piping stdout to app.log and keeping terminal active.",
      "expected_output": "[1] 14502",
      "common_mistakes": "Forgetting the ampersand, which locks your foreground session.",
      "tips": "Ensure the target log file has write permission before starting the background redirection."
    }
  ],
  "lessons": [
    {
      "id": 1,
      "title": "1. Create Capstone Workspace",
      "definition": "The Capstone Project combines directories setup, variables configuration, and permissions.",
      "explanation": "Create nested subfolders inside capstone to structure source codes, variables configurations, and backup stores.",
      "instruction": "Create directories: capstone/src, capstone/configs, and capstone/backups using mkdir.",
      "example": "mkdir -p project/app project/config project/logs",
      "expected": "",
      "hint": "Type: mkdir -p capstone/src capstone/configs capstone/backups",
      "solution": "mkdir -p capstone/src capstone/configs capstone/backups",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    },
    {
      "id": 2,
      "title": "2. Create Server Configuration",
      "definition": "Configuration files store system parameters, environment variables, and ports settings.",
      "explanation": "Use echo to populate a simple server.conf file mapping PORT=8080.",
      "instruction": "Write PORT=8080 into capstone/configs/server.conf.",
      "example": "echo 'ENV=dev' > config.txt",
      "expected": "",
      "hint": "Type: echo 'PORT=8080' > capstone/configs/server.conf",
      "solution": "echo 'PORT=8080' > capstone/configs/server.conf",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    },
    {
      "id": 3,
      "title": "3. Create Application Script",
      "definition": "Shell scripts automate system operations, status reporting, and background processes.",
      "explanation": "Create app.sh that prints status outputs, loop delays, and log paths.",
      "instruction": "Write shebang and a startup message into capstone/src/app.sh.",
      "example": "echo -e '#!/bin/bash\\necho \"Started\"' > script.sh",
      "expected": "",
      "hint": "Type: echo -e '#!/bin/bash\\necho \"App starting on port 8080...\"' > capstone/src/app.sh",
      "solution": "echo -e '#!/bin/bash\\necho \"App starting on port 8080...\"' > capstone/src/app.sh",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    },
    {
      "id": 4,
      "title": "4. Set Execution Permissions",
      "definition": "Execution flags allow scripts to run directly from shell pathways.",
      "explanation": "Add execute (+x) permission flag to the application script.",
      "instruction": "Make the script capstone/src/app.sh executable.",
      "example": "chmod +x backup.sh",
      "expected": "",
      "hint": "Type: chmod +x capstone/src/app.sh",
      "solution": "chmod +x capstone/src/app.sh",
      "difficulty": "Advanced",
      "estimated_duration": "4m"
    },
    {
      "id": 5,
      "title": "5. Create Administration Account",
      "definition": "Administrative operations require dedicated restricted service accounts.",
      "explanation": "Add a new simulation system user account named devops_admin.",
      "instruction": "Add a new system user named devops_admin. (Use simulated useradd)",
      "example": "useradd admin_user",
      "expected": "",
      "hint": "Type: useradd devops_admin",
      "solution": "useradd devops_admin",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    },
    {
      "id": 6,
      "title": "6. Reassign Workspace Ownership",
      "definition": "Securing configurations requires assigning file ownership to the service user.",
      "explanation": "Use chown to reassign the capstone folder tree owner to devops_admin.",
      "instruction": "Recursively assign ownership of the capstone folder to devops_admin.",
      "example": "chown -R admin_user /var/www",
      "expected": "",
      "hint": "Type: chown -R devops_admin capstone",
      "solution": "chown -R devops_admin capstone",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    },
    {
      "id": 7,
      "title": "7. Lock Configuration Secrets",
      "definition": "Configuration values containing passwords or ports should be owner-read only.",
      "explanation": "chmod 600 restricts access to only the file owner, hiding parameters from other system users.",
      "instruction": "Change capstone/configs/server.conf permissions to 600.",
      "example": "chmod 600 auth.json",
      "expected": "",
      "hint": "Type: chmod 600 capstone/configs/server.conf",
      "solution": "chmod 600 capstone/configs/server.conf",
      "difficulty": "Advanced",
      "estimated_duration": "4m"
    },
    {
      "id": 8,
      "title": "8. Write Archival Script",
      "definition": "Backup scripts copy source structures into compressed storage archives.",
      "explanation": "Create backup.sh containing simple files cloning steps.",
      "instruction": "Write shebang and copy instructions to capstone/src/backup.sh.",
      "example": "echo -e '#!/bin/bash\\ntar -czf backup.tar.gz src/' > backup.sh",
      "expected": "",
      "hint": "Type: echo -e '#!/bin/bash\\ncp -R capstone/src capstone/backups/' > capstone/src/backup.sh",
      "solution": "echo -e '#!/bin/bash\\ncp -R capstone/src capstone/backups/' > capstone/src/backup.sh",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    },
    {
      "id": 9,
      "title": "9. Script Executable Flag",
      "definition": "Backup utilities must be executable to run inside automation cron loops.",
      "explanation": "Add execution permission flag to backup.sh.",
      "instruction": "Set executable permissions on capstone/src/backup.sh.",
      "example": "chmod +x deploy.sh",
      "expected": "",
      "hint": "Type: chmod +x capstone/src/backup.sh",
      "solution": "chmod +x capstone/src/backup.sh",
      "difficulty": "Advanced",
      "estimated_duration": "4m"
    },
    {
      "id": 10,
      "title": "10. Test System Backup",
      "definition": "Validating backups before deployment checks copy scripts syntax.",
      "explanation": "Run backup.sh command to copy source directories into backup folders.",
      "instruction": "Run the backup script using the bash interpreter.",
      "example": "bash deploy.sh",
      "expected": "",
      "hint": "Type: bash capstone/src/backup.sh",
      "solution": "bash capstone/src/backup.sh",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    },
    {
      "id": 11,
      "title": "11. Verify Network Ports Bindings",
      "definition": "Verify active port allocations using ss or netstat.",
      "explanation": "Confirm which socket ports are active and open.",
      "instruction": "Display active TCP listening socket routes.",
      "example": "netstat -plnt",
      "expected": "State",
      "hint": "Type: ss -lnt",
      "solution": "ss -lnt",
      "difficulty": "Advanced",
      "estimated_duration": "4m"
    },
    {
      "id": 12,
      "title": "12. Create Log Rotator",
      "definition": "Log rotation clears old outputs preventing disk depletion.",
      "explanation": "Write rotation scripts to empty log files periodically.",
      "instruction": "Create capstone/src/rotate.sh containing echo command clearing app logs.",
      "example": "echo -e '#!/bin/bash\\ncat /dev/null > error.log' > rotate.sh",
      "expected": "",
      "hint": "Type: echo -e '#!/bin/bash\\necho \"\" > capstone/app.log' > capstone/src/rotate.sh",
      "solution": "echo -e '#!/bin/bash\\necho \"\" > capstone/app.log' > capstone/src/rotate.sh",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    },
    {
      "id": 13,
      "title": "13. Deploy Application Daemon",
      "definition": "Running scripts in background launches them as persistent services.",
      "explanation": "Launch app.sh redirecting outputs to capstone/app.log.",
      "instruction": "Launch capstone/src/app.sh in background, redirecting stdout to capstone/app.log.",
      "example": "bash script.sh > out.log &",
      "expected": "[1]",
      "hint": "Type: bash capstone/src/app.sh > capstone/app.log &",
      "solution": "bash capstone/src/app.sh > capstone/app.log &",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    },
    {
      "id": 14,
      "title": "14. Inspect Active Log Output",
      "definition": "tail views trailing parts of active logs to diagnose startup issues.",
      "explanation": "Prints log tail configurations containing application output lines.",
      "instruction": "Inspect active log output of capstone/app.log.",
      "example": "tail -n 10 server.log",
      "expected": "App starting on port 8080...",
      "hint": "Type: cat capstone/app.log",
      "solution": "cat capstone/app.log",
      "difficulty": "Advanced",
      "estimated_duration": "4m"
    },
    {
      "id": 15,
      "title": "15. Complete Capstone Review",
      "definition": "Final validation of running background configurations and variables settings.",
      "explanation": "Run process audit to check background execution is active.",
      "instruction": "Expose background jobs list status to verify app completion.",
      "example": "ps aux | grep script",
      "expected": "Running",
      "hint": "Type: jobs",
      "solution": "jobs",
      "difficulty": "Advanced",
      "estimated_duration": "5m"
    }
  ],
  "exercises": [
    {
      "title": "Full system backup automation",
      "problem": "Create a scheduled backup task that copies your config files to the backup drive every hour.",
      "difficulty": "Advanced",
      "hint": "Use a cron expression or a while loop containing sleep.",
      "expected_result": "Autosave backup file instances visible in backups/.",
      "objective": "Integrate scheduling automation scripts."
    },
    {
      "title": "Reassign and inspect permissions",
      "problem": "Check chown modifications results recursively to ensure all subfiles are restricted.",
      "difficulty": "Intermediate",
      "hint": "Inspect using `ls -laR capstone`.",
      "expected_result": "Owner show as devops_admin for all directories.",
      "objective": "Learn verification patterns."
    },
    {
      "title": "Simulate log rotation failures",
      "problem": "Test log rotator output if target log path does not exist, and write error logs.",
      "difficulty": "Advanced",
      "hint": "Evaluate directory check before truncating.",
      "expected_result": "Outputs error logs when missing directories are tested.",
      "objective": "Integrate error handlers inside automation utilities."
    },
    {
      "title": "Audit active network ports",
      "problem": "Inspect listening sockets on the host before and after starting your app daemon.",
      "difficulty": "Intermediate",
      "hint": "Compare `ss -lnt` output frames.",
      "expected_result": "Port 8080 binds only when daemon script is running.",
      "objective": "Master ports lifecycle debugging."
    },
    {
      "title": "Background daemon validation",
      "problem": "Audit variables export parameters mapping within a running background job.",
      "difficulty": "Advanced",
      "hint": "Run `ps -ef | grep app.sh`.",
      "expected_result": "Confirm PID matches active jobs list.",
      "objective": "Master background debugging."
    },
    {
      "title": "Secure workspace cleanup",
      "problem": "Safely archive all configuration files before truncating workspace blocks.",
      "difficulty": "Intermediate",
      "hint": "Run cp backups before executing deletions.",
      "expected_result": "Files successfully backed up before cleanup.",
      "objective": "Learn safe environment management practices."
    }
  ],
  "quiz": [
    {
      "question": "What is the primary role of the Capstone project?",
      "options": [
        "Deploy and scale clusters",
        "Integrate file operations, permissions, scripting, and networking into a deployment scenario",
        "Configure AWS networks gateways",
        "Write frontend frameworks pages"
      ],
      "answer": "Integrate file operations, permissions, scripting, and networking into a deployment scenario",
      "explanation": "The capstone aggregates all sysadmin skills to establish a production environment from scratch.",
      "incorrect_explanations": {
        "Deploy and scale clusters": "This is a Kubernetes task, not a basic Linux capstone.",
        "Configure AWS networks gateways": "This is a cloud engineer path module.",
        "Write frontend frameworks pages": "DevLab frontend relies on Next.js pages, not sysadmin commands."
      }
    },
    {
      "question": "What permission setting is set on config files to ensure they are owner-read only?",
      "options": ["777", "755", "600", "444"],
      "answer": "600",
      "explanation": "600 (owner read/write) blocks all group and public reads, protecting access keys.",
      "incorrect_explanations": {
        "777": "Permits public writes and is highly insecure.",
        "755": "Allows everyone to read and execute the file.",
        "444": "Makes the file read-only for everyone, including the owner."
      }
    },
    {
      "question": "Which flag is appended to chown to recursively modify ownership inside folders?",
      "options": ["-r", "-v", "-f", "-R"],
      "answer": "-R",
      "explanation": "-R is the standard recursive flag for ownership and permission changes.",
      "incorrect_explanations": {
        "-r": "Not the correct recursion flag.",
        "-v": "Verbose logs changes details.",
        "-f": "Force option."
      }
    },
    {
      "question": "How do you run a shell script in the background while redirecting stdout logs?",
      "options": [
        "bash script.sh > output.log &",
        "bash script.sh >> output.log",
        "bash script.sh & > output.log",
        "systemctl start script.sh"
      ],
      "answer": "bash script.sh > output.log &",
      "explanation": "> output.log redirects stdout, and & tells the shell to run it in the background.",
      "incorrect_explanations": {
        "bash script.sh >> output.log": "Runs script in the foreground, locking the terminal.",
        "bash script.sh & > output.log": "Syntax is invalid since the ampersand should be at the end.",
        "systemctl start script.sh": "systemctl only runs configured system services scripts, not raw path files."
      }
    },
    {
      "question": "What is the purpose of log rotation?",
      "options": [
        "Increase application execution speed",
        "Prevent disk space depletion by archiving/truncating log files",
        "Encrypt logs directories contents",
        "Transmit log outputs to database tables"
      ],
      "answer": "Prevent disk space depletion by archiving/truncating log files",
      "explanation": "Active logs are truncated or rotated to keep storage consumption within boundary configurations.",
      "incorrect_explanations": {
        "Increase application execution speed": "Has no effect on execution speed.",
        "Encrypt logs directories contents": "Rotators do not encrypt files.",
        "Transmit log outputs to database tables": "Rotators write to file storage, not DB."
      }
    },
    {
      "question": "Which command is used to inspect active TCP socket binds?",
      "options": ["ip route", "ss -lnt", "ps aux", "jobs"],
      "answer": "ss -lnt",
      "explanation": "ss -lnt lists all active TCP listening sockets.",
      "incorrect_explanations": {
        "ip route": "Displays gateway routing information.",
        "ps aux": "Lists active processes.",
        "jobs": "Lists shell background tasks."
      }
    },
    {
      "question": "True or False: Deleting a log file is always identical to truncating it using `echo > file`.",
      "options": ["True", "False"],
      "answer": "False",
      "explanation": "Deleting standard logs breaks the process holding the file descriptor, whereas truncating clears contents safely.",
      "incorrect_explanations": {
        "True": "Deleting files causes log write failures until process restarts."
      }
    },
    {
      "question": "Which directory commonly stores deployment executable script source files?",
      "options": ["configs/", "src/", "backups/", "logs/"],
      "answer": "src/",
      "explanation": "src/ (source) is the standard folder for project binaries and script files.",
      "incorrect_explanations": {
        "configs/": "Used for configuration files, not script source files.",
        "backups/": "Used for archived files.",
        "logs/": "Used for operational log files."
      }
    },
    {
      "question": "What is the function of the `jobs` command in process controls?",
      "options": ["Displays CPU cycles", "Lists background tasks spawned by the current shell", "Terminates stuck processes", "Configures network routes"],
      "answer": "Lists background tasks spawned by the current shell",
      "explanation": "jobs lists active shell-controlled processes like sleep or bg tasks.",
      "incorrect_explanations": {
        "Displays CPU cycles": "top or ps displays CPU cycles.",
        "Terminates stuck processes": "kill terminates processes.",
        "Configures network routes": "ip route handles routing."
      }
    },
    {
      "question": "Scenario: You deployed an application daemon in background redirecting to `app.log`. What command lets you audit the real-time startup lines?",
      "options": [
        "cat app.log",
        "tail -f app.log",
        "ss -lntp",
        "ps aux"
      ],
      "answer": "tail -f app.log",
      "explanation": "tail -f follows the file in real-time as lines are appended, displaying startup logs.",
      "incorrect_explanations": {
        "cat app.log": "Prints static contents once, does not trace active updates.",
        "ss -lntp": "Audits active ports, does not output file log texts.",
        "ps aux": "Audits active PIDs, does not display app console logs."
      }
    }
  ],
  "resources": {
    "summary": "The Capstone project integrates nested directories creation, file permissions restriction chmod 600, owner delegation chown -R, background execution script redirects, port checks ss, and logs rotation script validations.",
    "cheat_sheet": "mkdir -p [dirs] - build paths\nchmod 600 [file] - restrict permissions\nchown -R [owner] [dir] - change owner recursively\nbash [script].sh > [log] &\nss -lnt - check ports\njobs - check background jobs",
    "commands_table": [
      {"name": "chown", "syntax": "chown -R [owner] [path]", "description": "Delegates workspace ownership recursively."},
      {"name": "ss", "syntax": "ss -lnt", "description": "Verifies network listening socket binds."},
      {"name": "jobs", "syntax": "jobs", "description": "Audits active background jobs states."}
    ],
    "revision_notes": [
      "Always secure secrets using chmod 600 before launching scripts.",
      "Redirect stdout using > filename, and stderr using 2> filename.",
      "Verify jobs status inside terminal to confirm daemon loops remain active."
    ],
    "beginner_mistakes": [
      "Forgetting to allocate execution permissions on backup.sh.",
      "Deleting files instead of truncating them when working with active process descriptors."
    ],
    "best_practices": [
      "Create modular directories architectures for clean microservice separation.",
      "Deploy background processes using restricted user accounts instead of root."
    ],
    "interview_questions": [
      {"question": "How do you verify if a process is running in the background?", "answer": "Run jobs command or ps aux grep searches."},
      {"question": "How do you append both stdout and stderr to a log file?", "answer": "Use command >> file.log 2>&1."}
    ],
    "additional_practice": [
      "Build a complete multi-user workspace secure configuration directory tree.",
      "Write a backup cron job utility replicating deployment setups."
    ],
    "books": [
      {"title": "DevOps Handbook by Gene Kim", "description": "Core textbook for automation and system architectures."}
    ],
    "documentation": [
      {"title": "GNU Coreutils System Reference", "url": "https://www.gnu.org/software/coreutils/"}
    ],
    "external_resources": [
      {"title": "Linux Automation Capstones Guides", "url": "https://linuxacademy.com/"}
    ]
  }
}

with open(os.path.join(base_path, "linux-capstone-project.json"), "w", encoding="utf-8") as f:
    json.dump(capstone_data, f, indent=2, ensure_ascii=False)
print("Enriched capstone JSON.")
