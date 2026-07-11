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
  BookOpen,
  ArrowRight,
  Clipboard,
  Lightbulb,
  Award,
  Terminal as TerminalIcon,
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
  const [activeTab, setActiveTab] = useState<"theory" | "examples" | "lab" | "exercises" | "quiz">("theory");

  // Quiz States
  const [quizAnswers, setQuizAnswers] = useState<Record<number, string>>({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizScore, setQuizScore] = useState(0);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Fetch active session query
  const { data: session, isLoading: isLoadingSession } = useQuery<LabSession | null>({
    queryKey: ["active_linux_session", courseSlug],
    queryFn: () => labSessionService.getActiveLinuxSession(courseSlug),
  });

  // Fetch course details query (reusable schema containing theory, examples, quiz, exercises & lessons list)
  const { data: details, isLoading: isLoadingDetails } = useQuery<any>({
    queryKey: ["course_details", courseSlug],
    queryFn: () => labSessionService.getCourseDetails(courseSlug),
  });

  const lessons = details?.lessons || [];
  const theory = details?.theory || "";
  const examples = details?.interactive_examples || [];
  const exercises = details?.exercises || [];
  const quiz = details?.quiz || [];

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
      
      const nextIndex = lessons.findIndex((l: any) => l.id > lastCompletedId);
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
        queryClient.invalidateQueries({ queryKey: ["academies_list"] });
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

  const isCompleted = (id: number) => {
    return progress?.completed_lessons?.includes(id) || false;
  };

  const handleCopyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleQuizSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let correctCount = 0;
    quiz.forEach((q: any, idx: number) => {
      if (quizAnswers[idx] === q.answer) {
        correctCount++;
      }
    });
    setQuizScore(correctCount);
    setQuizSubmitted(true);
  };

  const isCourseComplete = progress?.percentage === 100;

  if (isLoadingDetails || isLoadingProgress) {
    return (
      <DashboardShell>
        <div className="flex h-[50vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardShell>
    );
  }

  if (!details || lessons.length === 0 || !activeTask) {
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

  const tabs = [
    { id: "theory", label: "1. Theory & Overview" },
    { id: "examples", label: "2. Interactive Examples" },
    { id: "lab", label: "3. Hands-on Lab" },
    { id: "exercises", label: "4. Exercises" },
    { id: "quiz", label: "5. Module Quiz" }
  ] as const;

  return (
    <DashboardShell>
      {/* Breadcrumbs Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1.5 text-xs text-muted-foreground">
          <Link href="/labs" className="hover:text-foreground transition-colors flex items-center gap-1">
            <ArrowLeft className="h-3 w-3" />
            <span>Catalog Explorer</span>
          </Link>
          <span className="text-muted-foreground/50">/</span>
          <span className="text-foreground font-semibold">{courseTitle}</span>
        </div>

        {/* Progress Pill */}
        <div className="flex items-center space-x-2 text-xs bg-primary/10 border border-primary/20 px-3 py-1 rounded-full text-primary font-bold">
          <Award className="h-3.5 w-3.5" />
          <span>{progress?.percentage || 0}% Complete</span>
        </div>
      </div>

      {/* Tabs Layout Row */}
      <div className="flex border-b border-border/60 pb-px gap-1 overflow-x-auto scrollbar-none">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === t.id
                ? "border-primary text-primary font-bold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      {activeTab === "theory" && (
        <div className="max-w-3xl rounded-xl border border-border bg-card p-8 shadow-sm space-y-6 animate-fade-in">
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground">Overview & Theoretical Concepts</h2>
            <p className="text-xs text-muted-foreground">Learn the fundamental structure before executing commands in the sandbox environment.</p>
          </div>
          <div className="prose prose-sm dark:prose-invert text-xs text-foreground/80 leading-relaxed space-y-4">
            {theory.split("\n\n").map((para: string, i: number) => (
              <p key={i}>{para}</p>
            ))}
          </div>
          <div className="pt-4 border-t border-border/40 flex justify-end">
            <Button
              className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md flex items-center space-x-1.5"
              onClick={() => setActiveTab("examples")}
            >
              <span>Continue to Examples</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}

      {activeTab === "examples" && (
        <div className="max-w-3xl rounded-xl border border-border bg-card p-8 shadow-sm space-y-6 animate-fade-in">
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground">Interactive Syntaxes & Examples</h2>
            <p className="text-xs text-muted-foreground">Review command structures and click to copy them for usage inside the hands-on lab sandbox later.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {examples.map((ex: any, idx: number) => (
              <div key={idx} className="p-4 bg-muted/40 border border-border/50 rounded-xl space-y-2 text-left relative hover:bg-muted/60 transition-colors">
                <div className="flex justify-between items-center">
                  <code className="text-xs font-bold text-primary font-mono">{ex.command}</code>
                  <button
                    onClick={() => handleCopyToClipboard(ex.command, idx)}
                    className="p-1 text-muted-foreground hover:text-primary transition-colors cursor-pointer"
                    title="Copy command"
                  >
                    {copiedIndex === idx ? (
                      <Check className="h-3.5 w-3.5 text-emerald-500" />
                    ) : (
                      <Clipboard className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
                <p className="text-[11px] text-muted-foreground leading-normal">{ex.description}</p>
              </div>
            ))}
          </div>
          <div className="pt-4 border-t border-border/40 flex justify-end">
            <Button
              className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md flex items-center space-x-1.5"
              onClick={() => setActiveTab("lab")}
            >
              <span>Start Hands-on Lab</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}

      {activeTab === "lab" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start animate-fade-in">
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
                {lessons.map((task: any, i: number) => (
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
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                    <Lightbulb className="h-3 w-3 text-amber-500" />
                    <span>Syntax Example (Generic)</span>
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
                {activeTask.expected && (
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                      Expected Outcome
                    </span>
                    <pre className="text-[10px] bg-muted/80 p-2.5 rounded border border-border/40 font-mono text-muted-foreground overflow-x-auto">
                      {activeTask.expected}
                    </pre>
                  </div>
                )}

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

            {/* Stepper Footer Trigger */}
            {isCourseComplete && (
              <div className="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl flex items-center justify-between gap-4">
                <div className="text-xs">
                  <p className="font-bold text-indigo-700 dark:text-indigo-400">All Lab Steps Verified!</p>
                  <p className="text-muted-foreground mt-0.5">Proceed to the supplementary exercises section.</p>
                </div>
                <Button
                  size="sm"
                  className="bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs font-bold shrink-0"
                  onClick={() => setActiveTab("exercises")}
                >
                  <span>Continue</span>
                  <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            )}
          </div>

          {/* Right Side: Sandbox Terminal (stays active in background) */}
          <div className="lg:col-span-7 space-y-6">
            {isLoadingSession ? (
              <div className="rounded-xl border border-border bg-card p-12 text-center animate-pulse">
                <div className="h-8 bg-muted w-1/3 rounded mx-auto mb-4" />
                <div className="h-[450px] bg-muted rounded-xl w-full" />
              </div>
            ) : !session ? (
              <div className="rounded-xl border border-border bg-card p-8 text-center space-y-6 shadow-sm">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 border border-primary/20">
                  <TerminalIcon className="h-6 w-6 text-primary" />
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
      )}

      {activeTab === "exercises" && (
        <div className="max-w-3xl rounded-xl border border-border bg-card p-8 shadow-sm space-y-6 animate-fade-in">
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground">Supplementary Practical Exercises</h2>
            <p className="text-xs text-muted-foreground">Test your knowledge with these offline exercise suggestions in the command line window.</p>
          </div>
          <div className="space-y-3">
            {exercises.map((ex: any, idx: number) => (
              <div key={idx} className="flex items-start space-x-3 p-4 bg-card border border-border rounded-xl">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-[10px] shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <p className="text-xs text-foreground/80 leading-relaxed">{ex.description}</p>
              </div>
            ))}
          </div>
          <div className="pt-4 border-t border-border/40 flex justify-end">
            <Button
              className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md flex items-center space-x-1.5"
              onClick={() => setActiveTab("quiz")}
            >
              <span>Take Module Quiz</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}

      {activeTab === "quiz" && (
        <div className="max-w-3xl rounded-xl border border-border bg-card p-8 shadow-sm space-y-6 animate-fade-in">
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground">Interactive Module Quiz</h2>
            <p className="text-xs text-muted-foreground">Select choices to validate your command structure understanding.</p>
          </div>

          <form onSubmit={handleQuizSubmit} className="space-y-6">
            {quiz.map((q: any, idx: number) => (
              <div key={idx} className="p-5 border border-border bg-card rounded-xl space-y-3">
                <p className="text-xs font-bold text-foreground leading-normal flex items-start gap-2">
                  <span className="text-primary shrink-0">Q{idx + 1}.</span>
                  <span>{q.question}</span>
                </p>
                <div className="grid grid-cols-1 gap-2 pt-1">
                  {q.options.map((opt: string) => {
                    const isSelected = quizAnswers[idx] === opt;
                    return (
                      <label
                        key={opt}
                        className={`flex items-center space-x-3 p-3 rounded-lg border text-xs cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-primary/5 border-primary text-primary font-semibold"
                            : "bg-muted/10 border-border/80 text-muted-foreground hover:bg-muted/30"
                        }`}
                      >
                        <input
                          type="radio"
                          name={`quiz-${idx}`}
                          value={opt}
                          checked={isSelected}
                          onChange={() => {
                            if (!quizSubmitted) {
                              setQuizAnswers((prev) => ({ ...prev, [idx]: opt }));
                            }
                          }}
                          className="accent-primary h-3.5 w-3.5 cursor-pointer shrink-0"
                          disabled={quizSubmitted}
                        />
                        <span>{opt}</span>
                      </label>
                    );
                  })}
                </div>

                {quizSubmitted && (
                  <div className="pt-2 text-[11px] font-bold">
                    {quizAnswers[idx] === q.answer ? (
                      <span className="text-emerald-600 flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Correct Answer
                      </span>
                    ) : (
                      <span className="text-red-500 flex items-center gap-1">
                        <AlertCircle className="h-3.5 w-3.5" /> Incorrect. Correct Answer: <code className="bg-red-500/10 px-1.5 py-0.5 rounded font-mono">{q.answer}</code>
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}

            {!quizSubmitted ? (
              <div className="pt-4 border-t border-border/40 flex justify-end">
                <Button
                  type="submit"
                  disabled={Object.keys(quizAnswers).length < quiz.length}
                  className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md px-6 cursor-pointer"
                >
                  Submit Answers
                </Button>
              </div>
            ) : (
              <div className="pt-6 border-t border-border/40 space-y-4 animate-fade-in text-center">
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl inline-block max-w-sm mx-auto">
                  <h4 className="text-sm font-bold text-emerald-600">Quiz Completed!</h4>
                  <p className="text-xs text-muted-foreground mt-1">
                    You scored <span className="font-bold text-foreground">{quizScore}</span> out of <span className="font-bold text-foreground">{quiz.length}</span> correct answers.
                  </p>
                </div>
                <div>
                  <Link href="/labs">
                    <Button className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md px-6">
                      Finish Module & Return
                    </Button>
                  </Link>
                </div>
              </div>
            )}
          </form>
        </div>
      )}
    </DashboardShell>
  );
}
