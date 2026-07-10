"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { labSessionService, LabSession } from "@/services/lab-session.service";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Terminal } from "@/components/ui/terminal";
import { Button } from "@/components/ui/button";
import {
  ChevronLeft,
  ChevronRight,
  Play,
  StopCircle,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ArrowLeft,
  Clock,
  Code,
  Check,
  Loader2,
} from "lucide-react";

interface TaskData {
  id: number;
  title: string;
  explanation: string;
  instruction: string;
  example: string;
  expected: string;
  hint: string;
}

const LINUX_TASKS: TaskData[] = [
  {
    id: 1,
    title: "1. Navigation (pwd)",
    explanation: "Before managing directories, you must know where you are located. In Linux, your current location is referred to as the Working Directory. The pwd (print working directory) command prints your absolute path.",
    instruction: "Run the pwd command in the terminal to inspect your current directory.",
    example: "pwd",
    expected: "/home/student",
    hint: "Run exact command: pwd",
  },
  {
    id: 2,
    title: "2. Working Directories (ls)",
    explanation: "The ls command lists the contents of a directory. By default, it hides files starting with a dot (hidden configuration files). The -a flag instructs ls to display all files, including hidden entries.",
    instruction: "List all contents inside your home directory including hidden configurations using ls -a.",
    example: "ls [options] [path]",
    expected: "Output showing . .. .bashrc .profile welcome.txt drafts/ old_logs/",
    hint: "Run exact command: ls -a",
  },
  {
    id: 3,
    title: "3. Files (touch)",
    explanation: "The touch command creates empty files or updates access modification timestamps on existing ones.",
    instruction: "Create an empty text file named note.txt using touch.",
    example: "touch filename.txt",
    expected: "Successfully created note.txt in /home/student.",
    hint: "Run exact command: touch note.txt",
  },
  {
    id: 4,
    title: "4. Directories (mkdir)",
    explanation: "To group files and structures, you create directories. The mkdir (make directory) command creates folders.",
    instruction: "Create a directory named backup in your home path.",
    example: "mkdir folder_name",
    expected: "Directory /home/student/backup is created.",
    hint: "Run exact command: mkdir backup",
  },
  {
    id: 5,
    title: "5. Copy (cp)",
    explanation: "The cp command copies files from a source path to a destination path.",
    instruction: "Copy note.txt into the backup directory under the name note_copy.txt.",
    example: "cp src.txt dest.txt",
    expected: "Copy is generated inside the backup subfolder.",
    hint: "Run exact command: cp note.txt backup/note_copy.txt",
  },
  {
    id: 6,
    title: "6. Move (mv)",
    explanation: "The mv command moves files or directories from one location to another. Unlike copy, the source is removed.",
    instruction: "Move the note_copy.txt file back to your home directory /home/student.",
    example: "mv src_file.txt destination_folder/",
    expected: "note_copy.txt resides in /home/student, no longer in backup/.",
    hint: "Run exact command: mv backup/note_copy.txt .",
  },
  {
    id: 7,
    title: "7. Rename (mv)",
    explanation: "In Linux, renaming is also done using the mv command by moving a file to a new name in the same path.",
    instruction: "Rename note_copy.txt in your home directory to log.txt.",
    example: "mv old_name.txt new_name.txt",
    expected: "note_copy.txt is renamed to log.txt.",
    hint: "Run exact command: mv note_copy.txt log.txt",
  },
  {
    id: 8,
    title: "8. Delete (rm)",
    explanation: "The rm (remove) command deletes files permanently. Be careful, there is no Recycle Bin!",
    instruction: "Delete the original note.txt file.",
    example: "rm filename.txt",
    expected: "note.txt is removed from your filesystem.",
    hint: "Run exact command: rm note.txt",
  },
  {
    id: 9,
    title: "9. Viewing Files (cat)",
    explanation: "The cat (concatenate) command reads contents of text files and prints them directly to the console stream.",
    instruction: "Print the contents of log.txt using cat.",
    example: "cat filename.txt",
    expected: "Blank output or contents printed to stdout.",
    hint: "Run exact command: cat log.txt",
  },
  {
    id: 10,
    title: "10. Permissions (chmod)",
    explanation: "In Linux, permissions dictate read (r), write (w), and execute (x) states for owner, group, and others. The chmod command updates these file mode bits (e.g. 600 limits access to owner only).",
    instruction: "Restrict log.txt permissions to owner read/write only (600).",
    example: "chmod permissions_octal filename.txt",
    expected: "Permissions updated. verifying ls -l shows -rw-------.",
    hint: "Run exact command: chmod 600 log.txt",
  },
  {
    id: 11,
    title: "11. Users (id)",
    explanation: "The id command details identifiers, group associations, and owner names for the current active account.",
    instruction: "Inspect your active identity information using id.",
    example: "id",
    expected: "uid=1000(student) gid=1000(student) details.",
    hint: "Run exact command: id",
  },
  {
    id: 12,
    title: "12. Groups (groups)",
    explanation: "The groups command prints a list of all user group memberships for the current user.",
    instruction: "Check what groups you are associated with.",
    example: "groups",
    expected: "student sudo",
    hint: "Run exact command: groups",
  },
  {
    id: 13,
    title: "13. Searching (grep)",
    explanation: "The grep command filters files for string matches. It prints matching lines containing the search pattern.",
    instruction: "Search for the keyword 'student' in log.txt using grep.",
    example: "grep 'search_string' filename.txt",
    expected: "Filtered lines printed.",
    hint: "Run exact command: grep student log.txt",
  },
  {
    id: 14,
    title: "14. Pipes (|)",
    explanation: "Pipes (|) send output of one command as the input to another command, enabling complex command chains.",
    instruction: "Pipe directory files list to grep to locate log.txt.",
    example: "command1 | command2",
    expected: "log.txt is printed.",
    hint: "Run exact command: ls | grep log.txt",
  },
  {
    id: 15,
    title: "15. Redirection (>)",
    explanation: "Redirection operators write stdout directly into files. '>' overwrites a file; '>>' appends text.",
    instruction: "Write the text 'DevOps' directly into a new file named dynamic.txt.",
    example: "echo \"text\" > filename.txt",
    expected: "dynamic.txt file contains 'DevOps'.",
    hint: "Run exact command: echo \"DevOps\" > dynamic.txt",
  },
  {
    id: 16,
    title: "16. Environment Variables",
    explanation: "Environment variables store config states globally. Use 'export KEY=VALUE' to set variables.",
    instruction: "Export an environment variable named REGISTRY with value 'local'.",
    example: "export VARIABLE_NAME=value",
    expected: "REGISTRY=local is visible in printenv outputs.",
    hint: "Run exact command: export REGISTRY=local",
  },
  {
    id: 17,
    title: "17. Processes (ps)",
    explanation: "The ps command lists active process instances running under the current terminal shell.",
    instruction: "View running system processes using ps.",
    example: "ps [options]",
    expected: "List showing bash and ps processes.",
    hint: "Run exact command: ps",
  },
  {
    id: 18,
    title: "18. Networking (ip route)",
    explanation: "DevOps requires networking tasks. The ip route command views active gateways routing tables.",
    instruction: "Inspect routing configurations using ip route.",
    example: "ip route",
    expected: "Default route details.",
    hint: "Run exact command: ip route",
  },
  {
    id: 19,
    title: "19. Directory Deletions",
    explanation: "To delete directories containing files, use rm with recursive (-r) and force (-f) flags.",
    instruction: "Recursively delete the backup directory.",
    example: "rm -rf folder_name",
    expected: "backup/ folder deleted.",
    hint: "Run exact command: rm -rf backup",
  },
  {
    id: 20,
    title: "20. Workspace Cleanup",
    explanation: "Finally, check your workspace directories status. Only log.txt and dynamic.txt should remain.",
    instruction: "Execute ls -la to check final directories state.",
    example: "ls -la",
    expected: "backup directory is gone, note.txt is gone.",
    hint: "Run exact command: ls -la",
  },
];

export default function LinuxBasicsLabPage() {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(0);
  const [showHint, setShowHint] = useState(false);
  
  // Track tasks completion states locally
  const [completedTasks, setCompletedTasks] = useState<Record<number, boolean>>({});
  const [validationMsg, setValidationMsg] = useState<{ success: boolean; text: string } | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Sync active session query
  const { data: session, isLoading: isLoadingSession } = useQuery<LabSession | null>({
    queryKey: ["active_linux_session"],
    queryFn: labSessionService.getActiveLinuxSession,
  });

  // Launch mutation
  const launchMutation = useMutation({
    mutationFn: labSessionService.launchLinuxLab,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["active_linux_session"] });
      setValidationMsg(null);
    },
  });

  // Stop mutation
  const stopMutation = useMutation({
    mutationFn: (id: string) => labSessionService.stopLinuxLab(id),
    onSuccess: () => {
      queryClient.setQueryData(["active_linux_session"], null);
      setCompletedTasks({});
      setValidationMsg(null);
    },
  });

  // Load completion states from localStorage on session start
  useEffect(() => {
    if (session) {
      const saved = localStorage.getItem(`completed_linux_${session.id}`);
      if (saved) {
        setCompletedTasks(JSON.parse(saved));
      }
    } else {
      setCompletedTasks({});
    }
  }, [session]);

  const activeTask = LINUX_TASKS[currentStep];

  const handleVerify = async () => {
    if (!session) return;
    setIsValidating(true);
    setValidationMsg(null);
    try {
      const res = await labSessionService.validateLinuxTask(session.id, activeTask.id);
      if (res.success) {
        const updated = { ...completedTasks, [activeTask.id]: true };
        setCompletedTasks(updated);
        localStorage.setItem(`completed_linux_${session.id}`, JSON.stringify(updated));
        setValidationMsg({ success: true, text: res.message });
      } else {
        setValidationMsg({ success: false, text: res.message });
      }
    } catch (err: any) {
      setValidationMsg({
        success: false,
        text: err.response?.data?.detail || "Validation engine connection refused.",
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleNext = () => {
    if (currentStep < LINUX_TASKS.length - 1) {
      setCurrentStep(currentStep + 1);
      setShowHint(false);
      setValidationMsg(null);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      setShowHint(false);
      setValidationMsg(null);
    }
  };

  return (
    <DashboardShell>
      {/* Header Breadcrumbs */}
      <div className="flex items-center space-x-1.5 text-xs text-muted-foreground">
        <Link href="/labs" className="hover:text-foreground transition-colors">
          Explorer
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span className="text-foreground font-semibold">Linux Basics</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Side: Syllabus Stepper (Instructions) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-border/40">
              <h2 className="text-sm font-bold text-foreground">Guided Instructions</h2>
              <span className="text-xs font-semibold text-primary">
                Step {currentStep + 1} of {LINUX_TASKS.length}
              </span>
            </div>

            {/* Stepper Dots bar */}
            <div className="flex flex-wrap gap-1">
              {LINUX_TASKS.map((task, i) => (
                <button
                  key={task.id}
                  onClick={() => {
                    setCurrentStep(i);
                    setShowHint(false);
                    setValidationMsg(null);
                  }}
                  className={`h-2.5 w-2.5 rounded-full border transition-all cursor-pointer ${
                    currentStep === i
                      ? "bg-primary border-primary scale-125"
                      : completedTasks[task.id]
                      ? "bg-emerald-500 border-emerald-500"
                      : "bg-muted border-border hover:bg-muted/80"
                  }`}
                  title={task.title}
                />
              ))}
            </div>

            {/* Task Card Detail */}
            <div className="space-y-4 pt-2">
              <h3 className="text-base font-bold text-foreground leading-tight">
                {activeTask.title}
              </h3>
              
              <p className="text-xs text-muted-foreground leading-relaxed">
                {activeTask.explanation}
              </p>

              {/* Example Command Box - Displayed ABOVE the Goal Box */}
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                  Example Command
                </span>
                <pre className="text-xs bg-[#1C1824] text-[#EFEBF4] p-3 rounded-lg border border-border/40 font-mono overflow-x-auto shadow-inner">
                  {activeTask.example}
                </pre>
              </div>

              {/* Task Goal Box */}
              <div className="p-4 bg-muted/40 border border-border/50 rounded-lg space-y-2">
                <div className="flex items-center text-xs font-bold text-primary">
                  <Code className="h-3.5 w-3.5 mr-1.5" />
                  <span>Exercise Task</span>
                </div>
                <p className="text-xs font-semibold text-foreground leading-relaxed">
                  {activeTask.instruction}
                </p>
              </div>

              {/* Expected Output */}
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                  Expected Outcome
                </span>
                <pre className="text-[10px] bg-muted/80 p-2.5 rounded border border-border/40 font-mono text-muted-foreground overflow-x-auto">
                  {activeTask.expected}
                </pre>
              </div>

              {/* Collapsible Hint */}
              <div className="pt-2">
                <button
                  onClick={() => setShowHint(!showHint)}
                  className="text-xs font-semibold text-primary hover:underline flex items-center space-x-1 cursor-pointer"
                >
                  <HelpCircle className="h-3.5 w-3.5" />
                  <span>{showHint ? "Hide Hint" : "Need a Hint?"}</span>
                </button>
                {showHint && (
                  <p className="text-xs font-mono bg-primary/5 text-primary border border-primary/20 p-2.5 rounded mt-2 leading-relaxed">
                    {activeTask.hint}
                  </p>
                )}
              </div>
            </div>

            {/* Validation Message Banner */}
            {validationMsg && (
              <div
                className={`p-3 border rounded-lg text-xs flex items-start space-x-2 ${
                  validationMsg.success
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-600"
                    : "bg-red-500/10 border-red-500/20 text-red-500"
                }`}
              >
                {validationMsg.success ? (
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                ) : (
                  <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
                )}
                <span className="leading-relaxed font-semibold">{validationMsg.text}</span>
              </div>
            )}

            {/* Verify Controls */}
            <div className="flex items-center justify-between pt-4 border-t border-border/40 gap-4">
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePrev}
                  disabled={currentStep === 0}
                  className="rounded-md"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNext}
                  disabled={currentStep === LINUX_TASKS.length - 1}
                  className="rounded-md"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>

              <Button
                disabled={!session || isValidating}
                onClick={handleVerify}
                className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md px-4"
              >
                {isValidating ? (
                  <>
                    <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                    Checking...
                  </>
                ) : completedTasks[activeTask.id] ? (
                  <>
                    <Check className="mr-1.5 h-3.5 w-3.5" />
                    Completed
                  </>
                ) : (
                  "Verify Task"
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Right Side: Sandbox Terminal viewport */}
        <div className="lg:col-span-7 space-y-6">
          {isLoadingSession ? (
            /* Loading sandbox details */
            <div className="rounded-xl border border-border bg-card p-12 text-center animate-pulse">
              <div className="h-8 bg-muted w-1/3 rounded mx-auto mb-4" />
              <div className="h-[450px] bg-muted rounded-xl w-full" />
            </div>
          ) : !session ? (
            /* Stopped State Launcher Card */
            <div className="rounded-xl border border-border bg-card p-8 text-center space-y-6 shadow-sm">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 border border-primary/20">
                <Code className="h-6 w-6 text-primary" />
              </div>
              <div className="space-y-2 max-w-sm mx-auto">
                <h2 className="text-lg font-bold text-foreground">Linux Sandbox Console</h2>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Start your isolated Ubuntu 24.04 command line container. Files and configurations are wiped automatically when terminated.
                </p>
              </div>

              <Button
                disabled={launchMutation.isPending}
                onClick={() => launchMutation.mutate()}
                className="bg-primary hover:bg-primary/95 text-primary-foreground font-bold text-xs py-2.5 px-6 rounded-md shadow flex items-center space-x-2 mx-auto"
              >
                {launchMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Spinning up Container...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    <span>Launch Linux Lab</span>
                  </>
                )}
              </Button>
            </div>
          ) : (
            /* Active Sandbox View */
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between bg-card border border-border p-4 rounded-xl shadow-sm gap-4">
                <div className="flex items-center space-x-3">
                  <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                  <div>
                    <h3 className="text-xs font-bold text-foreground">Active Sandbox Session</h3>
                    <p className="text-[10px] text-muted-foreground">ID: {session.id.substring(0, 8)}...</p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="flex items-center text-xs text-muted-foreground">
                    <Clock className="h-4 w-4 mr-1 text-primary" />
                    <span>Active Session</span>
                  </div>

                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={stopMutation.isPending}
                    onClick={() => stopMutation.mutate(session.id)}
                    className="bg-red-500 hover:bg-red-600 text-white text-xs font-bold rounded-md flex items-center space-x-1"
                  >
                    {stopMutation.isPending ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <>
                        <StopCircle className="h-3.5 w-3.5" />
                        <span>Terminate</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Live Terminal Widget */}
              <Terminal
                sessionId={session.id}
                onClose={() => queryClient.invalidateQueries({ queryKey: ["active_linux_session"] })}
              />
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
