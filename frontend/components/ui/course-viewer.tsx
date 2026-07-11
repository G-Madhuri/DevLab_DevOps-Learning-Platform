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

const getParentTechnologyId = (slug: string) => {
  if (slug.startsWith("linux-") || slug.startsWith("bash-") || slug.includes("linux")) {
    return "linux";
  }
  if (slug.startsWith("docker-") || slug.includes("docker")) {
    return "docker";
  }
  if (slug.startsWith("kubernetes-") || slug.includes("kubernetes")) {
    return "kubernetes";
  }
  if (slug.startsWith("git-") || slug.includes("git")) {
    return "git";
  }
  if (slug.startsWith("terraform-") || slug.includes("terraform")) {
    return "terraform";
  }
  if (slug.startsWith("aws-") || slug.includes("aws")) {
    return "aws";
  }
  if (slug.startsWith("azure-") || slug.includes("azure")) {
    return "azure";
  }
  if (slug.startsWith("ansible-") || slug.includes("ansible")) {
    return "ansible";
  }
  if (slug.startsWith("jenkins-") || slug.includes("jenkins")) {
    return "jenkins";
  }
  if (slug.startsWith("monitoring-") || slug.includes("monitoring") || slug.includes("prometheus")) {
    return "monitoring";
  }
  if (slug.startsWith("observability-") || slug.includes("observability") || slug.includes("elk")) {
    return "observability";
  }
  return slug;
};

export function CourseViewer({ courseSlug, courseTitle }: CourseViewerProps) {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [validationMsg, setValidationMsg] = useState<{ success: boolean; text: string } | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "theory" | "examples" | "lab" | "exercises" | "quiz" | "resources">("overview");

  // Quiz States
  const [quizAnswers, setQuizAnswers] = useState<Record<number, string>>({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizScore, setQuizScore] = useState(0);
  const [quizPassed, setQuizPassed] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Finish Module Toast
  const [showFinishToast, setShowFinishToast] = useState(false);
  const [toastTimer, setToastTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  // Completed Tabs Tracking
  const [completedTabs, setCompletedTabs] = useState<Record<string, boolean>>({});



  // Fetch active session query
  const { data: session, isLoading: isLoadingSession } = useQuery<LabSession | null>({
    queryKey: ["active_linux_session", getParentTechnologyId(courseSlug)],
    queryFn: () => labSessionService.getActiveLinuxSession(getParentTechnologyId(courseSlug)),
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

  // Sync completed tabs from progress
  useEffect(() => {
    if (progress) {
      const tabsMap: Record<string, boolean> = {};
      progress.completed_lessons.forEach((item: any) => {
        if (typeof item === "string") {
          tabsMap[item] = true;
        }
      });
      setCompletedTabs(tabsMap);
    } else {
      setCompletedTabs({});
    }
  }, [progress]);

  // Complete tab mutation
  const completeTabMutation = useMutation({
    mutationFn: (tabId: string) => labSessionService.completeCourseTab(courseSlug, tabId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["course_progress", courseSlug] });
      queryClient.invalidateQueries({ queryKey: ["academies_list"] });
    },
  });

  useEffect(() => {
    const observerOptions = {
      root: null, // viewport
      rootMargin: "0px",
      threshold: 0.1, // trigger as soon as bottom element enters even slightly
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const tabId = entry.target.getAttribute("data-tab-id");
          if (tabId && !completedTabs[tabId]) {
            completeTabMutation.mutate(tabId);
          }
        }
      });
    }, observerOptions);

    const targets = ["overview", "theory", "examples", "exercises"];
    targets.forEach((id) => {
      const el = document.getElementById(`bottom-detector-${id}`);
      if (el) {
        observer.observe(el);
      }
    });

    return () => {
      observer.disconnect();
    };
  }, [activeTab, courseSlug, completedTabs]);

  // Sync current step with last uncompleted lesson index
  useEffect(() => {
    if (progress && lessons.length > 0) {
      const numericCompleted = progress.completed_lessons.filter((x: any) => typeof x === "number");
      const lastCompletedId = numericCompleted.length > 0 
        ? Math.max(...numericCompleted) 
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
    mutationFn: () => labSessionService.launchLinuxLab(getParentTechnologyId(courseSlug)),
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
      const res = await labSessionService.validateLinuxTask(session.id, activeTask.id, courseSlug);
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

  const handleFinishModule = () => {
    if (showFinishToast) return;
    setShowFinishToast(true);
    const t = setTimeout(() => setShowFinishToast(false), 10000);
    setToastTimer(t);
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
    const passed = correctCount >= 8;
    setQuizPassed(passed);
    setQuizSubmitted(true);
    if (passed) {
      completeTabMutation.mutate("quiz");
    }
  };

  const handleQuizRetry = () => {
    setQuizAnswers({});
    setQuizSubmitted(false);
    setQuizScore(0);
    setQuizPassed(false);
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
    { id: "overview", label: "1. Overview" },
    { id: "theory", label: "2. Theory" },
    { id: "examples", label: "3. Interactive Examples" },
    { id: "lab", label: "4. Hands-on Lab" },
    { id: "exercises", label: "5. Practice Exercises" },
    { id: "quiz", label: "6. Module Quiz" },
    { id: "resources", label: "7. Resources" }
  ] as const;

  return (
    <DashboardShell>
      {/* Breadcrumbs Navigation */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-1.5 text-xs text-muted-foreground">
          <Link href="/labs" className="hover:text-foreground transition-colors flex items-center gap-1">
            <ArrowLeft className="h-3 w-3" />
            <span>Catalog Explorer</span>
          </Link>
          <span className="text-muted-foreground/50">/</span>
          <span className="text-foreground font-semibold">{courseTitle}</span>
        </div>
        <div className="flex items-center space-x-2 text-xs bg-primary/10 border border-primary/20 px-3 py-1 rounded-full text-primary font-bold">
          <Award className="h-3.5 w-3.5" />
          <span>{progress?.percentage || 0}% Complete</span>
        </div>
      </div>

      {/* Tabs Layout Row */}
      <div className="flex border-b border-border/60 pb-px gap-1 overflow-x-auto scrollbar-none mb-8">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap flex items-center gap-1.5 ${
              activeTab === t.id
                ? "border-primary text-primary font-bold"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <span>{t.label}</span>
            {completedTabs[t.id] && (
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 fill-emerald-500/10 shrink-0" />
            )}
          </button>
        ))}
      </div>

      {/* Tab Contents */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start animate-fade-in">
          {/* Main Overview Content */}
          <div className="lg:col-span-8 space-y-6">
            <div className="rounded-xl border border-border bg-card p-8 shadow-sm space-y-6">
              <div className="space-y-2">
                <h2 className="text-lg font-bold text-foreground">Course Module Overview</h2>
                <p className="text-xs text-muted-foreground">Get oriented with what this module will teach you and why it matters in production.</p>
              </div>

              {/* Introduction Paragraphs */}
              <div className="space-y-4 text-xs text-foreground/80 leading-relaxed">
                {(details.overview?.introduction || [
                  "Welcome to this course module. Here we will introduce you to fundamental administration concepts and command layouts.",
                  "This topic is widely used in DevOps configurations, container orchestration, and server lifecycle automation."
                ]).map((p: string, idx: number) => (
                  <p key={idx}>{p}</p>
                ))}
              </div>

              {/* What You Will Learn */}
              <div className="space-y-3 pt-6 border-t border-border/40">
                <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">What You Will Learn</h3>
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-muted-foreground">
                  {(details.overview?.what_you_will_learn || [
                    "Understand core operations layout",
                    "Configure access nodes",
                    "Manage execution cycles"
                  ]).map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-primary shrink-0 mt-0.5">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Right Side Sidebar Metadata */}
          <div className="lg:col-span-4 space-y-6">
            <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-5 text-xs">
              <h3 className="font-bold text-foreground uppercase tracking-wider text-[10px] text-muted-foreground">Module Parameters</h3>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Difficulty:</span>
                  <span className="font-bold text-primary capitalize">{details.overview?.difficulty || "Beginner"}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Estimated Time:</span>
                  <span className="font-bold text-foreground flex items-center">
                    <Clock className="h-3.5 w-3.5 mr-1" />
                    {details.overview?.estimated_time || "45m"}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Prerequisites:</span>
                  <span className="font-bold text-foreground/80">{details.overview?.prerequisites || "None"}</span>
                </div>
              </div>

              {/* Learning Outcomes */}
              <div className="pt-4 border-t border-border/40 space-y-2">
                <span className="font-bold text-[10px] text-muted-foreground uppercase tracking-wider">Learning Outcomes</span>
                <ul className="space-y-1.5 text-muted-foreground">
                  {(details.overview?.learning_outcomes || [
                    "Confidently manage file resources",
                    "Understand shell environment variables"
                  ]).map((out: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                      <span>{out}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <Button
              className="w-full bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl flex items-center justify-center space-x-2 py-2.5 shadow-sm"
              onClick={() => setActiveTab("theory")}
            >
              <span>Start Learning Theory</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
          {/* Bottom detector for tab completion */}
          <div id="bottom-detector-overview" data-tab-id="overview" className="h-1 w-full" />
        </div>
      )}

      {activeTab === "theory" && (
        <div className="max-w-3xl space-y-6 animate-fade-in">
          <div className="rounded-xl border border-border bg-card p-8 shadow-sm space-y-6">
            <div className="space-y-2">
              <h2 className="text-lg font-bold text-foreground">Theoretical Deep-Dive</h2>
              <p className="text-xs text-muted-foreground">Understand the WHY behind these tools before running the hands-on environment.</p>
            </div>

            {/* Subtopics Cards rendering */}
            <div className="space-y-6">
              {((details.theory as any[]) || [
                {
                  title: "Theoretical Overview",
                  definition: "General definition of concepts.",
                  explanation: "Detailed guide on processes layouts.",
                  why_exists: "To automate deployments safely.",
                  where_used: "Configuring container runtimes.",
                  real_world_example: "Nginx web servers running in ports setups.",
                  best_practices: "Follow least privilege configurations.",
                  common_mistakes: "Using root privileges unnecessarily."
                }
              ]).map((sub, idx) => (
                <div key={idx} className="p-6 border border-border bg-card/65 rounded-xl space-y-4">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-foreground tracking-tight">{sub.title}</h3>
                    <p className="text-xs text-primary font-semibold">{sub.definition}</p>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed whitespace-pre-line">{sub.explanation}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-border/40 text-xs">
                    <div>
                      <span className="font-bold text-foreground block mb-0.5">Why It Exists:</span>
                      <p className="text-muted-foreground">{sub.why_exists}</p>
                    </div>
                    <div>
                      <span className="font-bold text-foreground block mb-0.5">Where It Is Used:</span>
                      <p className="text-muted-foreground">{sub.where_used}</p>
                    </div>
                  </div>

                  <div className="p-3 bg-muted/40 rounded-lg text-xs space-y-1 border border-border/30">
                    <span className="font-bold text-primary block">Real-World Case:</span>
                    <p className="text-foreground/90">{sub.real_world_example}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="bg-emerald-500/[0.02] border border-emerald-500/20 p-3 rounded-lg text-emerald-600">
                      <span className="font-bold block mb-1">✓ Best Practices</span>
                      <p className="text-muted-foreground text-[11px]">{sub.best_practices}</p>
                    </div>
                    <div className="bg-red-500/[0.02] border border-red-500/20 p-3 rounded-lg text-red-500">
                      <span className="font-bold block mb-1">✗ Common Beginner Mistakes</span>
                      <p className="text-muted-foreground text-[11px]">{sub.common_mistakes}</p>
                    </div>
                  </div>
                </div>
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
          {/* Bottom detector for tab completion */}
          <div id="bottom-detector-theory" data-tab-id="theory" className="h-1 w-full" />
        </div>
      )}

      {activeTab === "examples" && (
        <div className="max-w-3xl space-y-6 animate-fade-in">
          <div className="rounded-xl border border-border bg-card p-8 shadow-sm space-y-6">
            <div className="space-y-2">
              <h2 className="text-lg font-bold text-foreground">Interactive Command Examples</h2>
              <p className="text-xs text-muted-foreground">Review functional syntaxes and expected outputs. Click command boxes to copy them.</p>
            </div>

            <div className="grid grid-cols-1 gap-6">
              {examples.map((ex: any, idx: number) => (
                <div key={idx} className="p-5 border border-border bg-card/65 rounded-xl space-y-4">
                  <div className="flex justify-between items-start">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Example {idx + 1}</span>
                    <span className="text-xs font-bold text-foreground">{ex.objective}</span>
                  </div>

                  <div className="space-y-2">
                    {/* Click-to-copy terminal input box */}
                    <div
                      onClick={() => {
                        navigator.clipboard.writeText(ex.command);
                        setCopiedIndex(idx);
                        setTimeout(() => setCopiedIndex(null), 2000);
                      }}
                      className="group relative cursor-pointer font-mono text-xs bg-[#1C1824] text-[#EFEBF4] p-3 rounded-lg border border-border/40 flex justify-between items-center hover:border-primary/40 transition-colors shadow-inner"
                      title="Click to copy command"
                    >
                      <span>$ {ex.command}</span>
                      <span className="text-[9px] font-bold text-primary uppercase bg-primary/10 border border-primary/20 px-1.5 py-0.5 rounded group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                        {copiedIndex === idx ? "Copied!" : "Copy"}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Step-by-Step Explanation</span>
                    <p className="text-xs text-muted-foreground leading-relaxed">{ex.explanation}</p>
                  </div>

                  {ex.expected_output && (
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">Expected Terminal Output</span>
                      <pre className="text-[10px] bg-muted/80 p-3 rounded border border-border/40 font-mono text-muted-foreground overflow-x-auto leading-relaxed">
                        {ex.expected_output}
                      </pre>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-2 border-t border-border/40">
                    <div className="text-red-500">
                      <span className="font-bold">Common Mistakes:</span>
                      <p className="text-muted-foreground text-[11px]">{ex.common_mistakes || "Failing to type arguments."}</p>
                    </div>
                    <div className="text-amber-500">
                      <span className="font-bold">Pro Tip:</span>
                      <p className="text-muted-foreground text-[11px]">{ex.tips || "Combine flags where appropriate."}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-4 border-t border-border/40 flex justify-end">
              <Button
                className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md flex items-center space-x-1.5"
                onClick={() => setActiveTab("lab")}
              >
                <span>Launch Interactive Lab</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
          {/* Bottom detector for tab completion */}
          <div id="bottom-detector-examples" data-tab-id="examples" className="h-1 w-full" />
        </div>
      )}

      {/* Side-by-side terminal for Lab or Exercises */}
      {(activeTab === "lab" || activeTab === "exercises") && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start animate-fade-in">
          {/* Left Column: Lab instructions Stepper OR Exercises list */}
          <div className="lg:col-span-5 space-y-6">
            {activeTab === "lab" ? (
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-5">
                <div className="flex justify-between items-center border-b border-border/40 pb-3">
                  <h2 className="text-sm font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <Award className="h-4 w-4 text-primary" />
                    <span>Lab Environment Tasks</span>
                  </h2>
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

                {/* Task details */}
                <div className="space-y-4 pt-2">
                  {/* Heading */}
                  <h3 className="text-xs font-extrabold text-foreground uppercase tracking-wide">
                    {activeTask.title}
                  </h3>

                  {/* Definition */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">Definition</span>
                    <p className="text-xs text-foreground/80 leading-relaxed bg-muted/20 p-3 rounded-lg border border-border/30">
                      {activeTask.definition}
                    </p>
                  </div>

                  {/* Command */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">Command</span>
                    <div className="pt-0.5">
                      <code className="inline-block text-xs px-2.5 py-1 bg-primary/10 border border-primary/20 text-primary font-bold rounded font-mono">
                        {(() => {
                          const match = activeTask.title.match(/\(([^)]+)\)/);
                          return match ? match[1] : (activeTask.solution || activeTask.title.replace(/^\d+\.\s*/, ""));
                        })()}
                      </code>
                    </div>
                  </div>

                  {/* Explanation Collapsible */}
                  {activeTask.explanation && (
                    <div className="border border-border/30 rounded-lg bg-muted/10 overflow-hidden">
                      <button
                        type="button"
                        onClick={() => setShowExplanation(!showExplanation)}
                        className="w-full flex items-center justify-between p-3 text-xs font-semibold text-primary hover:bg-muted/20 transition-colors cursor-pointer"
                      >
                        <span className="flex items-center space-x-1.5">
                          <Code className="h-3.5 w-3.5" />
                          <span>Detailed Explanation</span>
                        </span>
                        {showExplanation ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                      {showExplanation && (
                        <div className="p-3 pt-0 text-xs text-muted-foreground border-t border-border/25 leading-relaxed bg-card animate-fadeIn whitespace-pre-line">
                          {activeTask.explanation}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Syntax Example / Command Syntax */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">Example Command-Syntax</span>
                    <pre className="text-xs bg-[#1C1824] text-[#EFEBF4] p-3 rounded-lg border border-border/40 font-mono overflow-x-auto shadow-inner">
                      {activeTask.example}
                    </pre>
                  </div>

                  {/* Task Goal Box */}
                  <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg space-y-2">
                    <div className="flex items-center text-xs font-bold text-primary">
                      <Code className="h-3.5 w-3.5 mr-1.5" />
                      <span>Your Task</span>
                    </div>
                    <p className="text-xs font-bold text-foreground leading-relaxed">
                      {activeTask.instruction}
                    </p>
                  </div>

                  {/* Expected Output */}
                  {activeTask.expected && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">
                        Expected Output
                      </span>
                      <pre className="text-[10px] bg-muted/80 p-2.5 rounded border border-border/40 font-mono text-muted-foreground overflow-x-auto leading-relaxed">
                        {activeTask.expected}
                      </pre>
                    </div>
                  )}

                  {/* Hint */}
                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={() => setShowHint(!showHint)}
                      className="text-xs font-semibold text-primary hover:underline flex items-center space-x-1 cursor-pointer"
                    >
                      <HelpCircle className="h-3.5 w-3.5" />
                      <span>{showHint ? "Hide Hint" : "Need a Hint?"}</span>
                    </button>
                    {showHint && (
                      <p className="text-xs font-mono bg-amber-500/5 text-amber-600 border border-amber-500/20 p-2.5 rounded mt-2 leading-relaxed">
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
            ) : (
              /* Exercises listing */
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-5">
                <div className="space-y-1">
                  <h2 className="text-sm font-bold text-foreground uppercase tracking-wider">Practice Exercises</h2>
                  <p className="text-xs text-muted-foreground">Optional, non-validated challenges to practice in the running terminal shell.</p>
                </div>

                <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
                  {exercises.map((ex: any, idx: number) => (
                    <div key={idx} className="p-4 border border-border/60 bg-muted/20 rounded-xl space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] font-bold text-primary uppercase">Exercise {idx + 1}: {ex.title}</span>
                        <span className="px-2 py-0.5 bg-muted border border-border/50 text-[9px] font-bold rounded text-muted-foreground capitalize">{ex.difficulty}</span>
                      </div>
                      <p className="text-xs font-semibold text-foreground/90 leading-relaxed">{ex.problem}</p>

                      <div className="pt-2 text-[11px] text-muted-foreground space-y-1 border-t border-border/40">
                        <p><span className="font-semibold text-foreground/80">Objective:</span> {ex.objective}</p>
                        <p><span className="font-semibold text-foreground/80">Expected:</span> {ex.expected_result}</p>
                        <p className="text-primary/90 font-mono"><span className="font-semibold text-foreground/80">Hint:</span> {ex.hint}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <Button
                  className="w-full bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md py-2 flex items-center justify-center space-x-1.5"
                  onClick={() => setActiveTab("quiz")}
                >
                  <span>Continue to Module Quiz</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
                {/* Bottom detector for tab completion */}
                <div id="bottom-detector-exercises" data-tab-id="exercises" className="h-1 w-full" />
              </div>
            )}
          </div>

          {/* Right Column: Sandbox Terminal Console */}
          <div className="lg:col-span-7 space-y-6">
            {isLoadingSession ? (
              <div className="rounded-xl border border-border bg-card p-12 text-center animate-pulse">
                <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">Checking active session configurations...</p>
              </div>
            ) : !session ? (
              <div className="rounded-xl border border-border bg-card p-8 text-center space-y-6">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 border border-primary/20">
                  <TerminalIcon className="h-6 w-6 text-primary" />
                </div>
                <div className="space-y-2 max-w-sm mx-auto">
                  <h2 className="text-base font-black text-foreground">{courseTitle} Sandbox</h2>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Start a temporary Linux containers shell process to execute task operations. Terminals sessions persist in the background.
                  </p>
                </div>
                <Button
                  disabled={launchMutation.isPending}
                  onClick={() => launchMutation.mutate()}
                  className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl px-6 py-2.5 shadow-sm transition-transform hover:scale-[1.01] cursor-pointer"
                >
                  {launchMutation.isPending ? "Spawning Environment..." : "Launch Lab"}
                </Button>
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-card overflow-hidden shadow-md flex flex-col h-[65vh]">
                <div className="bg-[#18141F] border-b border-[#2E2838] px-4 py-3 flex justify-between items-center shrink-0">
                  <div className="flex items-center space-x-2">
                    <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[10px] font-extrabold text-white uppercase tracking-widest">
                      Linux Container Sandbox (Active)
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => stopMutation.mutate(session.id)}
                      disabled={stopMutation.isPending}
                      className="h-7 text-[10px] font-bold border-red-500/20 text-red-500 hover:bg-red-500/10 rounded"
                    >
                      {stopMutation.isPending ? (
                        "Stopping..."
                      ) : (
                        <>
                          <StopCircle className="h-3.5 w-3.5 mr-1" />
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

      {activeTab === "quiz" && (
        <div className="max-w-3xl space-y-6 animate-fade-in">
          <div className="rounded-xl border border-border bg-card p-8 shadow-sm space-y-6">
            <div className="space-y-2">
              <h2 className="text-lg font-bold text-foreground">Interactive Module Quiz</h2>
              <p className="text-xs text-muted-foreground">Complete this 10-question evaluation to test command line syntax and diagnostic scenarios comprehension.</p>
            </div>

            <form onSubmit={handleQuizSubmit} className="space-y-6">
              {quiz.map((q: any, idx: number) => {
                const isSelected = (opt: string) => quizAnswers[idx] === opt;
                return (
                  <div key={idx} className="p-6 border border-border bg-card/65 rounded-xl space-y-4">
                    <div className="flex items-start gap-2">
                      <span className="text-xs font-black text-primary bg-primary/10 border border-primary/20 h-5 w-5 rounded-full flex items-center justify-center shrink-0">
                        {idx + 1}
                      </span>
                      <p className="text-xs font-bold text-foreground leading-relaxed pt-0.5">
                        {q.question}
                      </p>
                    </div>

                    <div className="grid grid-cols-1 gap-2 pt-1">
                      {q.options.map((opt: string) => {
                        const selected = isSelected(opt);
                        return (
                          <label
                            key={opt}
                            className={`flex items-center space-x-3 p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                              selected
                                ? "bg-primary/5 border-primary text-primary font-bold shadow-sm"
                                : "bg-muted/10 border-border/80 text-muted-foreground hover:bg-muted/20"
                            }`}
                          >
                            <input
                              type="radio"
                              name={`quiz-${idx}`}
                              value={opt}
                              checked={selected}
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
                      <div className="p-4 bg-muted/40 rounded-lg text-xs space-y-2 border border-border/30">
                        <div className="font-bold flex items-center gap-1">
                          {quizAnswers[idx] === q.answer ? (
                            <span className="text-emerald-600 flex items-center gap-1">
                              <CheckCircle2 className="h-4 w-4" /> Correct Answer
                            </span>
                          ) : (
                            <span className="text-red-500 flex items-center gap-1">
                              <AlertCircle className="h-4 w-4" /> Incorrect Choice
                            </span>
                          )}
                        </div>
                        <p className="text-foreground/90 font-medium leading-relaxed">
                          <span className="font-bold text-foreground">Explanation: </span>
                          {q.explanation}
                        </p>

                        {/* Explain incorrect selections */}
                        {q.incorrect_explanations && (
                          <div className="text-[11px] text-muted-foreground pt-1 border-t border-border/20 space-y-1">
                            <span className="font-bold block text-foreground/80 mb-0.5">Why other options are wrong:</span>
                            {Object.entries(q.incorrect_explanations).map(([opt, desc]: any) => (
                              <p key={opt}>
                                <span className="font-semibold text-foreground/75 font-mono bg-muted px-1 rounded">{opt}:</span> {desc}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}

              {!quizSubmitted ? (
                <div className="pt-4 border-t border-border/40 flex justify-end">
                  <Button
                    type="submit"
                    disabled={Object.keys(quizAnswers).length < quiz.length}
                    className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl px-8 py-2.5 shadow-sm cursor-pointer"
                  >
                    Submit Quiz Answers
                  </Button>
                </div>
              ) : (
                <div className="pt-6 border-t border-border/40 space-y-4 animate-fade-in text-center">
                  {quizPassed ? (
                    <div className="p-5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl inline-block max-w-sm mx-auto">
                      <div className="text-2xl mb-2">🏆</div>
                      <h4 className="text-sm font-bold text-emerald-600">Quiz Passed!</h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        You scored <span className="font-bold text-foreground">{quizScore}</span> / <span className="font-bold text-foreground">{quiz.length}</span> — well done!
                      </p>
                    </div>
                  ) : (
                    <div className="p-5 bg-red-500/10 border border-red-500/20 rounded-xl inline-block max-w-sm mx-auto">
                      <div className="text-2xl mb-2">📝</div>
                      <h4 className="text-sm font-bold text-red-500">Score Below Passing</h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        You scored <span className="font-bold text-foreground">{quizScore}</span> / <span className="font-bold text-foreground">{quiz.length}</span>. You need at least <span className="font-bold text-primary">8/10</span> to pass.
                      </p>
                    </div>
                  )}
                  <div className="flex items-center justify-center gap-3 flex-wrap">
                    <Button
                      variant="outline"
                      className="text-xs font-bold rounded-md px-5 border-primary/30 text-primary hover:bg-primary/10 cursor-pointer"
                      onClick={handleQuizRetry}
                    >
                      Retry Quiz
                    </Button>
                    {quizPassed && (
                      <Button
                        className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md px-6 cursor-pointer"
                        onClick={() => setActiveTab("resources")}
                      >
                        Continue to Resources
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </form>
          </div>
        </div>
      )}

      {activeTab === "resources" && (
        <div className="max-w-3xl space-y-6 animate-fade-in">
          <div className="rounded-xl border border-border bg-card p-8 shadow-sm space-y-6">
            <div className="space-y-2">
              <h2 className="text-lg font-bold text-foreground">Module Resources & Cheat Sheets</h2>
              <p className="text-xs text-muted-foreground">Review key summaries, study command references, and search external documentations.</p>
            </div>

            {/* Resources Sections */}
            <div className="space-y-6 text-xs">
              {/* Summary */}
              <div className="p-4 bg-muted/40 border border-border/50 rounded-xl space-y-2">
                <span className="font-bold text-primary block uppercase tracking-wider text-[10px]">Module Summary</span>
                <p className="text-foreground/80 leading-relaxed">{details.resources?.summary || "Summary details loaded."}</p>
              </div>

              {/* Cheat Sheet */}
              {details.resources?.cheat_sheet && (
                <div className="space-y-2">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Quick Commands Cheat Sheet</span>
                  <pre className="p-4 bg-[#1C1824] text-[#EFEBF4] rounded-lg border border-border/40 font-mono overflow-x-auto leading-relaxed">
                    {details.resources.cheat_sheet}
                  </pre>
                </div>
              )}

              {/* Commands Table */}
              {details.resources?.commands_table && (
                <div className="space-y-2">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Command Reference Table</span>
                  <div className="overflow-x-auto border border-border/60 rounded-xl">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-muted/80 text-foreground font-bold border-b border-border/50">
                          <th className="p-3 text-[10px] uppercase">Command</th>
                          <th className="p-3 text-[10px] uppercase">Syntax</th>
                          <th className="p-3 text-[10px] uppercase">Description</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/40">
                        {details.resources.commands_table.map((row: any, i: number) => (
                          <tr key={i} className="hover:bg-muted/10">
                            <td className="p-3 font-bold font-mono text-primary">{row.name}</td>
                            <td className="p-3 font-mono text-foreground/80">{row.syntax}</td>
                            <td className="p-3 text-muted-foreground">{row.description}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Revision Notes & Best Practices */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                <div className="space-y-2">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Quick Revision Notes</span>
                  <ul className="space-y-2">
                    {(details.resources?.revision_notes || ["Review commands lists parameters"]).map((note: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-muted-foreground leading-normal">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{note}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="space-y-2">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Best Practices Checklist</span>
                  <ul className="space-y-2">
                    {(details.resources?.best_practices || ["Follow security boundaries rules"]).map((practice: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-muted-foreground leading-normal">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{practice}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Common Beginner Mistakes */}
              {details.resources?.beginner_mistakes && (
                <div className="p-4 bg-red-500/[0.02] border border-red-500/20 rounded-xl space-y-2">
                  <span className="font-bold text-red-500 block uppercase tracking-wider text-[10px]">Common Mistakes to Avoid</span>
                  <ul className="space-y-2">
                    {details.resources.beginner_mistakes.map((mistake: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-muted-foreground leading-normal">
                        <span className="text-red-500 font-bold shrink-0">•</span>
                        <span>{mistake}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Interview Questions */}
              {details.resources?.interview_questions && (
                <div className="space-y-2">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Sample Interview Questions</span>
                  <div className="space-y-3">
                    {details.resources.interview_questions.map((faq: any, i: number) => (
                      <div key={i} className="p-4 bg-muted/20 border border-border/50 rounded-xl space-y-1">
                        <p className="font-bold text-foreground">Q: {faq.question}</p>
                        <p className="text-muted-foreground leading-relaxed">A: {faq.answer}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Books & External Resources */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 border-t border-border/40">
                <div className="space-y-2">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Recommended Books</span>
                  <div className="space-y-2">
                    {(details.resources?.books || []).map((book: any, idx: number) => (
                      <div key={idx} className="space-y-0.5">
                        <span className="font-bold text-foreground/95 block">{book.title}</span>
                        <p className="text-muted-foreground text-[11px]">{book.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Documentation & Links</span>
                  <div className="space-y-2 text-[11px]">
                    {(details.resources?.documentation || []).map((link: any, idx: number) => (
                      <div key={idx}>
                        <a href={link.url} target="_blank" rel="noreferrer" className="text-primary hover:underline font-bold block">
                          {link.title} →
                        </a>
                      </div>
                    ))}
                    {(details.resources?.external_resources || []).map((link: any, idx: number) => (
                      <div key={idx}>
                        <a href={link.url} target="_blank" rel="noreferrer" className="text-primary hover:underline font-bold block">
                          {link.title} →
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Downloadable Notes Placeholder */}
              <div className="p-4 bg-muted/10 border border-dashed border-border rounded-xl text-center text-muted-foreground text-[11px]">
                <span>Downloadable PDF Cheat Sheets notes format placeholder (Coming Soon in later platform updates).</span>
              </div>
            </div>

            <div className="pt-6 border-t border-border/40 text-center">
              <Button
                onClick={handleFinishModule}
                className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl px-8 py-2.5 cursor-pointer"
              >
                Finish Module Course
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Finish Module Toast — bottom-right, closes in 10s */}
      {showFinishToast && (
        <div className="fixed bottom-6 right-6 z-50 animate-fade-in max-w-sm w-full">
          <div className="bg-card border border-border rounded-xl shadow-2xl p-4 flex items-start gap-3">
            <div className="shrink-0 h-8 w-8 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-lg">
              ℹ️
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-foreground mb-0.5">Complete All Content First</p>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Please complete all the Overview, Theory, Examples, Lab tasks, Exercises, and pass the Quiz (8/10) before finishing this module.
              </p>
            </div>
            <button
              onClick={() => {
                setShowFinishToast(false);
                if (toastTimer) clearTimeout(toastTimer);
              }}
              className="shrink-0 text-muted-foreground hover:text-foreground text-lg leading-none cursor-pointer"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
