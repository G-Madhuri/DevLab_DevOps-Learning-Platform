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
  ChevronDown,
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

interface CourseViewerProps {
  courseSlug: string;
  courseTitle: string;
}

export function CourseViewer({ courseSlug, courseTitle }: CourseViewerProps) {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [validationMsg, setValidationMsg] = useState<{ success: boolean; text: string } | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  // Fetch active session query
  const { data: session, isLoading: isLoadingSession } = useQuery<LabSession | null>({
    queryKey: ["active_linux_session", courseSlug],
    queryFn: () => labSessionService.getActiveLinuxSession(courseSlug),
  });

  // Fetch course lessons query
  const { data: lessons = [], isLoading: isLoadingLessons } = useQuery<any[]>({
    queryKey: ["course_lessons", courseSlug],
    queryFn: () => labSessionService.getCourseLessons(courseSlug),
  });

  // Fetch course progress query
  const { data: progress, isLoading: isLoadingProgress } = useQuery({
    queryKey: ["course_progress", courseSlug],
    queryFn: () => labSessionService.getCourseProgress(courseSlug),
  });

  // Sync current step with last uncompleted lesson index
  useEffect(() => {
    if (progress && lessons.length > 0) {
      const lastCompletedId = progress.completed_lessons.length > 0 
        ? Math.max(...progress.completed_lessons) 
        : 0;
      
      const nextIndex = lessons.findIndex(l => l.id > lastCompletedId);
      if (nextIndex !== -1) {
        setCurrentStep(nextIndex);
      } else {
        setCurrentStep(lessons.length - 1);
      }
    }
  }, [progress, lessons]);

  // Launch mutation
  const launchMutation = useMutation({
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["active_linux_session"] });
      queryClient.invalidateQueries({ queryKey: ["all_active_sessions"] });
      queryClient.invalidateQueries({ queryKey: ["user_sessions"] });
      queryClient.invalidateQueries({ queryKey: ["academies_list"] });
      setValidationMsg(null);
    },
    mutationFn: () => labSessionService.launchLinuxLab(courseSlug),
  });

  // Stop mutation
  const stopMutation = useMutation({
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["active_linux_session"] });
      queryClient.invalidateQueries({ queryKey: ["all_active_sessions"] });
      queryClient.invalidateQueries({ queryKey: ["user_sessions"] });
      queryClient.invalidateQueries({ queryKey: ["academies_list"] });
      setValidationMsg(null);
    },
    mutationFn: (id: string) => labSessionService.stopLinuxLab(id),
  });

  const activeTask = lessons[currentStep];

  const handleVerify = async () => {
    if (!session || !activeTask) return;
    setIsValidating(true);
    setValidationMsg(null);
    try {
      const res = await labSessionService.validateLinuxTask(session.id, activeTask.id);
      if (res.success) {
        setValidationMsg({ success: true, text: res.message });
        queryClient.invalidateQueries({ queryKey: ["course_progress", courseSlug] });
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
    if (currentStep < lessons.length - 1) {
      setCurrentStep(currentStep + 1);
      setShowHint(false);
      setShowExplanation(false);
      setValidationMsg(null);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      setShowHint(false);
      setShowExplanation(false);
      setValidationMsg(null);
    }
  };

  const isCompleted = (taskId: number) => {
    return progress?.completed_lessons?.includes(taskId) || false;
  };

  if (isLoadingLessons || isLoadingProgress) {
    return (
      <DashboardShell>
        <div className="flex flex-col items-center justify-center py-20 space-y-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-xs text-muted-foreground">Bootstrapping syllabus configs...</span>
        </div>
      </DashboardShell>
    );
  }

  if (lessons.length === 0 || !activeTask) {
    return (
      <DashboardShell>
        <div className="p-8 text-center bg-card border rounded-xl">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <h3 className="text-sm font-bold text-foreground">Course Configuration Failed</h3>
          <p className="text-xs text-muted-foreground mt-1">Failed to read lessons configurations from course folder.</p>
        </div>
      </DashboardShell>
    );
  }

  return (
    <DashboardShell>
      <div className="flex items-center space-x-1.5 text-xs text-muted-foreground">
        <Link href="/labs" className="hover:text-foreground transition-colors">
          Explorer
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span className="text-foreground font-semibold">{courseTitle}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Side: Syllabus Stepper */}
        <div className="lg:col-span-5 space-y-6">
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-border/40">
              <h2 className="text-sm font-bold text-foreground">Guided Instructions</h2>
              <span className="text-xs font-semibold text-primary">
                Step {currentStep + 1} of {lessons.length}
              </span>
            </div>

            {/* Stepper dots */}
            <div className="flex flex-wrap gap-1">
              {lessons.map((task, i) => (
                <button
                  key={task.id}
                  onClick={() => {
                    setCurrentStep(i);
                    setShowHint(false);
                    setShowExplanation(false);
                    setValidationMsg(null);
                  }}
                  className={`h-2.5 w-2.5 rounded-full border transition-all cursor-pointer ${
                    currentStep === i
                      ? "bg-primary border-primary scale-125"
                      : isCompleted(task.id)
                      ? "bg-emerald-500 border-emerald-500"
                      : "bg-muted border-border hover:bg-muted/80"
                  }`}
                  title={task.title}
                />
              ))}
            </div>

            {/* Tasks details */}
            <div className="space-y-4 pt-2">
              <h3 className="text-base font-bold text-foreground leading-tight">
                {activeTask.title}
              </h3>
              
              {activeTask.definition && (
                <p className="text-xs text-foreground/90 font-medium leading-relaxed">
                  {activeTask.definition}
                </p>
              )}

              {activeTask.explanation && (
                <div className="border border-border/30 rounded-lg bg-muted/10 overflow-hidden">
                  <button
                    onClick={() => setShowExplanation(!showExplanation)}
                    className="w-full flex items-center justify-between p-3 text-xs font-semibold text-primary hover:bg-muted/20 transition-colors cursor-pointer"
                  >
                    <span className="flex items-center space-x-1.5">
                      <Code className="h-3.5 w-3.5" />
                      <span>How it works (Command explanation)</span>
                    </span>
                    {showExplanation ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </button>
                  {showExplanation && (
                    <div className="p-3 pt-0 text-xs text-muted-foreground border-t border-border/25 leading-relaxed bg-card animate-fadeIn">
                      {activeTask.explanation}
                    </div>
                  )}
                </div>
              )}

              {/* Example Command Box */}
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

              {/* Hint */}
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

            {/* Validation Alert */}
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
                  disabled={currentStep === lessons.length - 1}
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
                ) : isCompleted(activeTask.id) ? (
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

        {/* Right Side: Sandbox Terminal */}
        <div className="lg:col-span-7 space-y-6">
          {isLoadingSession ? (
            <div className="rounded-xl border border-border bg-card p-12 text-center animate-pulse">
              <div className="h-8 bg-muted w-1/3 rounded mx-auto mb-4" />
              <div className="h-[450px] bg-muted rounded-xl w-full" />
            </div>
          ) : !session ? (
            <div className="rounded-xl border border-border bg-card p-8 text-center space-y-6 shadow-sm">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 border border-primary/20">
                <Code className="h-6 w-6 text-primary" />
              </div>
              <div className="space-y-2 max-w-sm mx-auto">
                <h2 className="text-lg font-bold text-foreground">{courseTitle} Sandbox</h2>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Start your isolated learning container environment. Any changes are automatically wiped when terminated.
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
                    <span>Spinning up Sandbox...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    <span>Launch Environment</span>
                  </>
                )}
              </Button>
            </div>
          ) : (
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

              <Terminal
                sessionId={session.id}
                onClose={() => queryClient.invalidateQueries({ queryKey: ["active_linux_session", courseSlug] })}
              />
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
