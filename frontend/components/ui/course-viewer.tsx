"use client";

import React, { useState, useEffect, useRef } from "react";
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
  Compass,
  Code,
  Check,
  Loader2,
  BookOpen,
  ArrowRight,
  Clipboard,
  Lightbulb,
  Award,
  Terminal as TerminalIcon,
  ExternalLink,
  Copy,
  FileText,
  Globe,
  Zap,
  Target,
  Info,
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

const DIFFICULTY_ORDER = ["easy", "beginner", "medium", "intermediate", "hard", "challenge"];
const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  beginner: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  medium: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  intermediate: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  hard: "bg-orange-500/10 text-orange-600 border-orange-500/20",
  challenge: "bg-red-500/10 text-red-500 border-red-500/20",
};
const DIFFICULTY_LABELS: Record<string, string> = {
  easy: "Easy",
  beginner: "Easy",
  medium: "Medium",
  intermediate: "Medium",
  hard: "Hard",
  challenge: "Challenge",
};

export function CourseViewer({ courseSlug, courseTitle }: CourseViewerProps) {
  const queryClient = useQueryClient();
  const [currentStep, setCurrentStep] = useState(0);
  const [showHint, setShowHint] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const [validationMsg, setValidationMsg] = useState<{ success: boolean; text: string } | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "concepts" | "examples" | "lab" | "exercises" | "quiz" | "resources">("overview");

  // Quiz States
  const [quizAnswers, setQuizAnswers] = useState<Record<number, string>>({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizScore, setQuizScore] = useState(0);
  const [quizPassed, setQuizPassed] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [cheatCopied, setCheatCopied] = useState(false);

  // Finish Module Toast
  const [showFinishToast, setShowFinishToast] = useState(false);
  const [toastTimer, setToastTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  // Completed Tabs Tracking
  const [completedTabs, setCompletedTabs] = useState<Record<string, boolean>>({});

  // Exercise hint tracking
  const [openExerciseHints, setOpenExerciseHints] = useState<Record<number, boolean>>({});

  // Fetch active session query
  const { data: session, isLoading: isLoadingSession } = useQuery<LabSession | null>({
    queryKey: ["active_linux_session", getParentTechnologyId(courseSlug)],
    queryFn: () => labSessionService.getActiveLinuxSession(getParentTechnologyId(courseSlug)),
  });

  // Fetch course details query
  const { data: details, isLoading: isLoadingDetails } = useQuery<any>({
    queryKey: ["course_details", courseSlug],
    queryFn: () => labSessionService.getCourseDetails(courseSlug),
  });

  const lessons = details?.lessons || [];
  // Support both "key_concepts" (new) and "theory" (legacy) field names
  const keyConcepts = details?.key_concepts || details?.theory || [];
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
      root: null,
      rootMargin: "0px",
      threshold: 0.1,
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

    const targets = ["overview", "concepts", "examples", "exercises"];
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

  const handleCopyCheatSheet = (text: string) => {
    navigator.clipboard.writeText(text);
    setCheatCopied(true);
    setTimeout(() => setCheatCopied(false), 2000);
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
    const passMark = Math.ceil(quiz.length * 0.8); // 80% pass mark
    const passed = correctCount >= passMark;
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

  // Group exercises by difficulty
  const groupedExercises = exercises.reduce((acc: Record<string, any[]>, ex: any) => {
    const level = (ex.difficulty || "medium").toLowerCase();
    if (!acc[level]) acc[level] = [];
    acc[level].push(ex);
    return acc;
  }, {} as Record<string, any[]>);

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
    { id: "concepts", label: "2. Key Concepts" },
    { id: "examples", label: "3. Examples" },
    { id: "lab", label: "4. Hands-on Lab" },
    { id: "exercises", label: "5. Practice Exercises" },
    { id: "quiz", label: "6. Module Quiz" },
    { id: "resources", label: "7. Resources" },
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

      {/* ============================================================ */}
      {/* TAB: OVERVIEW                                                 */}
      {/* ============================================================ */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start animate-fade-in">
          {/* Main Overview Content */}
          <div className="lg:col-span-8 space-y-6">
            <div className="rounded-xl border border-border bg-card p-8 shadow-sm space-y-6">
              <div className="space-y-2">
                <h2 className="text-lg font-bold text-foreground">Module Overview</h2>
                <p className="text-xs text-muted-foreground">What you will learn, why it matters, and what you will build.</p>
              </div>

              {/* Introduction — max 1 short paragraph */}
              <div className="text-sm text-foreground/80 leading-relaxed">
                {Array.isArray(details.overview?.introduction)
                  ? details.overview.introduction[0]
                  : details.overview?.introduction || "Welcome to this module."}
              </div>

              {/* Why this matters */}
              <div className="p-4 bg-primary/5 border border-primary/20 rounded-xl space-y-2">
                <span className="text-xs font-bold text-primary uppercase tracking-wider flex items-center gap-1.5">
                  <Zap className="h-3.5 w-3.5" /> Why This Matters
                </span>
                <p className="text-xs text-foreground/80 leading-relaxed">
                  {details.overview?.why_it_matters ||
                    "This topic is foundational to DevOps, cloud computing, and server management."}
                </p>
              </div>

              {/* Where it's used */}
              {details.overview?.industry_usage && (
                <div className="p-4 bg-muted/30 border border-border/40 rounded-xl space-y-2">
                  <span className="text-xs font-bold text-foreground/80 uppercase tracking-wider flex items-center gap-1.5">
                    <Globe className="h-3.5 w-3.5" /> Where It's Used in Industry
                  </span>
                  <p className="text-xs text-muted-foreground leading-relaxed">{details.overview.industry_usage}</p>
                </div>
              )}

              {/* What you will build */}
              {details.overview?.what_you_will_build && (
                <div className="p-4 bg-indigo-500/5 border border-indigo-500/20 rounded-xl space-y-2">
                  <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider flex items-center gap-1.5">
                    <Target className="h-3.5 w-3.5" /> What You Will Practice
                  </span>
                  <p className="text-xs text-muted-foreground leading-relaxed">{details.overview.what_you_will_build}</p>
                </div>
              )}

              {/* Learning Outcomes */}
              <div className="space-y-3 pt-4 border-t border-border/40">
                <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">Learning Outcomes</h3>
                <ul className="space-y-2">
                  {(details.overview?.learning_outcomes || details.overview?.what_you_will_learn || [
                    "Understand core operations",
                    "Configure access nodes",
                    "Manage execution cycles",
                  ]).map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-foreground/80">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Right Side Sidebar Metadata */}
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-5 text-xs">
              <h3 className="font-bold text-foreground uppercase tracking-wider text-[10px] text-muted-foreground">Module Info</h3>

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
                  <span className="font-bold text-foreground/80 text-right max-w-[60%]">{details.overview?.prerequisites || "None"}</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-3 text-xs">
              <h3 className="font-bold text-[10px] text-muted-foreground uppercase tracking-wider">Module Contents</h3>
              <div className="space-y-2 text-muted-foreground">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-3.5 w-3.5 text-primary" />
                  <span>{keyConcepts.length} Key Concepts</span>
                </div>
                <div className="flex items-center gap-2">
                  <Code className="h-3.5 w-3.5 text-primary" />
                  <span>{examples.length} Interactive Examples</span>
                </div>
                <div className="flex items-center gap-2">
                  <TerminalIcon className="h-3.5 w-3.5 text-primary" />
                  <span>{lessons.length} Lab Tasks</span>
                </div>
                <div className="flex items-center gap-2">
                  <Target className="h-3.5 w-3.5 text-primary" />
                  <span>{exercises.length} Practice Exercises</span>
                </div>
                <div className="flex items-center gap-2">
                  <Award className="h-3.5 w-3.5 text-primary" />
                  <span>{quiz.length} Quiz Questions</span>
                </div>
              </div>
            </div>

            <Button
              className="w-full bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl flex items-center justify-center space-x-2 py-2.5 shadow-sm"
              onClick={() => setActiveTab("concepts")}
            >
              <span>Start Learning</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
          <div id="bottom-detector-overview" data-tab-id="overview" className="h-1 w-full" />
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB: KEY CONCEPTS                                             */}
      {/* ============================================================ */}
      {activeTab === "concepts" && (
        <div className="max-w-5xl space-y-6 animate-fade-in">
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground">Key Concepts</h2>
            <p className="text-xs text-muted-foreground">
              Learn each concept clearly before moving to the hands-on lab. Click any command to copy it.
            </p>
          </div>

          {/* Concept Cards */}
          <div className="space-y-8">
            {(keyConcepts as any[]).map((sub, idx) => (
              <div key={idx} className="border border-border bg-card rounded-xl overflow-hidden shadow-sm">
                {/* Card Header */}
                <div className="bg-muted/40 border-b border-border/50 px-6 py-4 flex items-center gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold shrink-0">
                    {idx + 1}
                  </span>
                  <h3 className="text-sm font-bold text-foreground">{sub.title}</h3>
                </div>

                <div className="p-6 space-y-5">
                  {/* Definition */}
                  <div className="p-4 bg-primary/5 border-l-4 border-primary rounded-r-xl">
                    <span className="text-[10px] font-bold text-primary uppercase tracking-wider block mb-1">Definition</span>
                    <p className="text-sm text-foreground/90 leading-relaxed">{sub.definition}</p>
                  </div>

                  {/* Why Important — bullet list */}
                  {(sub.why_important || sub.why_exists) && (
                    <div className="p-4 bg-indigo-500/5 border border-indigo-500/20 rounded-xl space-y-2">
                      <span className="font-bold text-indigo-600 text-xs flex items-center gap-1.5">
                        <HelpCircle className="h-4 w-4" /> Why is this important?
                      </span>
                      {Array.isArray(sub.why_important) ? (
                        <ul className="space-y-1.5">
                          {sub.why_important.map((point: string, i: number) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                              <span className="text-indigo-500 font-bold shrink-0 mt-0.5">•</span>
                              <span>{point}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground leading-relaxed">{sub.why_important || sub.why_exists}</p>
                      )}
                    </div>
                  )}

                  {/* Explanation */}
                  {sub.explanation && (
                    <div className="text-sm text-foreground/80 leading-relaxed whitespace-pre-line space-y-2">
                      {sub.explanation}
                    </div>
                  )}

                  {/* Command Reference Cards */}
                  {sub.commands && sub.commands.length > 0 && (
                    <div className="space-y-3 pt-2 border-t border-border/40">
                      <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
                        <Code className="h-3.5 w-3.5 text-primary" /> Command Reference
                      </h4>
                      <div className="space-y-4">
                        {sub.commands.map((cmd: any, cIdx: number) => (
                          <div key={cIdx} className="border border-border/60 rounded-xl overflow-hidden bg-card/30">
                            {/* Command Header */}
                            <div className="bg-[#18141F] border-b border-[#2E2838] px-4 py-2.5 flex justify-between items-center">
                              <div className="flex items-center gap-3">
                                <code className="text-sm font-bold text-emerald-400 font-mono">{cmd.name}</code>
                                <span className="text-[10px] text-[#A89BC2] font-medium">{cmd.purpose}</span>
                              </div>
                              <span className="text-[9px] font-bold text-[#A89BC2] uppercase tracking-wider border border-[#2E2838] px-2 py-0.5 rounded">
                                {cmd.when_to_use?.slice(0, 30)}...
                              </span>
                            </div>

                            {/* Command Body */}
                            <div className="p-4 space-y-3 text-[12px]">
                              {/* Syntax + Parameters row */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                <div className="space-y-1">
                                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Syntax</span>
                                  <code className="block font-mono bg-muted px-3 py-1.5 rounded text-foreground/90 text-xs">
                                    {cmd.syntax}
                                  </code>
                                </div>
                                {cmd.parameters && (
                                  <div className="space-y-1">
                                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Parameters</span>
                                    <p className="text-muted-foreground leading-relaxed text-xs">{cmd.parameters}</p>
                                  </div>
                                )}
                              </div>

                              {/* Example */}
                              {cmd.example && (
                                <div className="space-y-1">
                                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Example</span>
                                  <div
                                    onClick={() => handleCopyToClipboard(cmd.example, cIdx * 100 + idx)}
                                    className="group relative cursor-pointer font-mono text-xs bg-[#1C1824] text-[#EFEBF4] p-3 rounded-lg border border-border/40 flex justify-between items-center hover:border-primary/40 transition-colors"
                                    title="Click to copy"
                                  >
                                    <span>$ {cmd.example}</span>
                                    <span className="text-[9px] font-bold text-primary uppercase bg-primary/10 border border-primary/20 px-1.5 py-0.5 rounded group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                                      {copiedIndex === cIdx * 100 + idx ? "Copied!" : "Copy"}
                                    </span>
                                  </div>
                                </div>
                              )}

                              {/* Expected Output */}
                              {cmd.expected_output && (
                                <div className="space-y-1">
                                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Expected Output</span>
                                  <pre className="text-xs bg-muted/80 p-3 rounded border border-border/30 font-mono text-muted-foreground overflow-x-auto leading-relaxed">
                                    {cmd.expected_output}
                                  </pre>
                                </div>
                              )}

                              {/* Output Explanation */}
                              {cmd.output_explanation && (
                                <p className="text-xs text-muted-foreground leading-relaxed bg-muted/20 px-3 py-2 rounded border border-border/20">
                                  <strong className="text-foreground/80">Explanation:</strong> {cmd.output_explanation}
                                </p>
                              )}

                              {/* Real-world use */}
                              {cmd.real_world_use && (
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                  <strong className="text-foreground/70">Real-world:</strong> {cmd.real_world_use}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Pro Tip / Best Practices / Common Mistakes */}
                  {(sub.pro_tip || sub.best_practices || sub.common_mistakes) && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 border-t border-border/30">
                      {sub.pro_tip && (
                        <div className="bg-amber-500/5 border border-amber-500/20 p-4 rounded-xl space-y-1.5">
                          <span className="font-bold text-amber-600 flex items-center gap-1 text-xs">
                            <Lightbulb className="h-3.5 w-3.5 shrink-0" /> Pro Tip
                          </span>
                          <p className="text-[11px] text-muted-foreground leading-relaxed">{sub.pro_tip}</p>
                        </div>
                      )}
                      {sub.best_practices && (
                        <div className="bg-emerald-500/5 border border-emerald-500/20 p-4 rounded-xl space-y-1.5">
                          <span className="font-bold text-emerald-600 flex items-center gap-1 text-xs">
                            <Check className="h-3.5 w-3.5 shrink-0" /> Best Practices
                          </span>
                          <p className="text-[11px] text-muted-foreground leading-relaxed">{sub.best_practices}</p>
                        </div>
                      )}
                      {sub.common_mistakes && (
                        <div className="bg-red-500/5 border border-red-500/20 p-4 rounded-xl space-y-1.5">
                          <span className="font-bold text-red-500 flex items-center gap-1 text-xs">
                            <AlertCircle className="h-3.5 w-3.5 shrink-0" /> Common Mistakes
                          </span>
                          <p className="text-[11px] text-muted-foreground leading-relaxed">{sub.common_mistakes}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Real-world example */}
                  {sub.real_world_example && (
                    <div className="p-4 bg-muted/20 border border-border/40 rounded-xl space-y-1">
                      <span className="font-bold text-foreground/80 text-xs flex items-center gap-1.5">
                        <Compass className="h-4 w-4" /> Real-world Example
                      </span>
                      <p className="text-xs text-muted-foreground leading-relaxed">{sub.real_world_example}</p>
                    </div>
                  )}

                  {/* Remember */}
                  {sub.remember && (
                    <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl space-y-1">
                      <span className="font-bold text-blue-600 text-xs flex items-center gap-1.5">
                        <Info className="h-4 w-4" /> Remember
                      </span>
                      <p className="text-xs text-muted-foreground leading-relaxed">{sub.remember}</p>
                    </div>
                  )}

                  {/* Summary */}
                  {sub.summary && (
                    <div className="pt-3 border-t border-border/30">
                      <p className="text-xs text-muted-foreground leading-relaxed bg-muted/10 px-4 py-3 rounded-lg border border-border/20">
                        <strong className="text-foreground/80">Quick Summary:</strong> {sub.summary}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-4 flex justify-end">
            <Button
              className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md flex items-center space-x-1.5"
              onClick={() => setActiveTab("examples")}
            >
              <span>Continue to Examples</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </div>
          <div id="bottom-detector-concepts" data-tab-id="concepts" className="h-1 w-full" />
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB: EXAMPLES                                                 */}
      {/* ============================================================ */}
      {activeTab === "examples" && (
        <div className="max-w-5xl space-y-6 animate-fade-in">
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground">Interactive Examples</h2>
            <p className="text-xs text-muted-foreground">
              Study each example carefully. Click any command to copy it, then try it in the lab.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-5">
            {examples.map((ex: any, idx: number) => (
              <div key={idx} className="border border-border bg-card rounded-xl overflow-hidden shadow-sm">
                {/* Example header */}
                <div className="bg-muted/40 border-b border-border/50 px-5 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground bg-muted border border-border/50 px-2 py-0.5 rounded">
                      Example {idx + 1}
                    </span>
                    <span className="text-sm font-semibold text-foreground">{ex.objective}</span>
                  </div>
                  {ex.difficulty && (
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border capitalize ${DIFFICULTY_COLORS[(ex.difficulty || "medium").toLowerCase()] || "bg-muted text-muted-foreground border-border/50"}`}>
                      {ex.difficulty}
                    </span>
                  )}
                </div>

                <div className="p-5 space-y-4">
                  {/* Scenario / What and Why */}
                  {ex.scenario && (
                    <div className="p-3 bg-primary/5 border border-primary/20 rounded-lg">
                      <p className="text-xs text-foreground/80 leading-relaxed">
                        <strong className="text-primary">Scenario: </strong>{ex.scenario}
                      </p>
                    </div>
                  )}

                  {/* Click-to-copy command */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Command</span>
                    <div
                      onClick={() => {
                        navigator.clipboard.writeText(ex.command);
                        setCopiedIndex(idx + 1000);
                        setTimeout(() => setCopiedIndex(null), 2000);
                      }}
                      className="group relative cursor-pointer font-mono text-sm bg-[#1C1824] text-[#EFEBF4] p-3.5 rounded-lg border border-border/40 flex justify-between items-center hover:border-primary/40 transition-colors shadow-inner"
                      title="Click to copy command"
                    >
                      <span>$ {ex.command}</span>
                      <span className="text-[9px] font-bold text-primary uppercase bg-primary/10 border border-primary/20 px-1.5 py-0.5 rounded group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                        {copiedIndex === idx + 1000 ? "Copied!" : "Copy"}
                      </span>
                    </div>
                  </div>

                  {/* Explanation */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">What this does</span>
                    <p className="text-xs text-muted-foreground leading-relaxed">{ex.explanation}</p>
                  </div>

                  {/* Expected output */}
                  {ex.expected_output && (
                    <div className="space-y-1.5">
                      <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">Expected Output</span>
                      <pre className="text-xs bg-muted/80 p-3 rounded border border-border/40 font-mono text-muted-foreground overflow-x-auto leading-relaxed">
                        {ex.expected_output}
                      </pre>
                    </div>
                  )}

                  {/* Output explanation */}
                  {ex.output_explanation && (
                    <p className="text-xs text-muted-foreground leading-relaxed bg-muted/20 px-3 py-2 rounded border border-border/20">
                      <strong className="text-foreground/80">Output explained: </strong>{ex.output_explanation}
                    </p>
                  )}

                  {/* Bottom row: real world use + mistakes + tips */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs pt-3 border-t border-border/40">
                    {ex.real_world_use && (
                      <div>
                        <span className="font-bold text-indigo-600 flex items-center gap-1 mb-1">
                          <Compass className="h-3 w-3" /> Real-world Use
                        </span>
                        <p className="text-muted-foreground text-[11px] leading-relaxed">{ex.real_world_use}</p>
                      </div>
                    )}
                    {ex.common_mistakes && (
                      <div>
                        <span className="font-bold text-red-500 flex items-center gap-1 mb-1">
                          <AlertCircle className="h-3 w-3" /> Common Mistakes
                        </span>
                        <p className="text-muted-foreground text-[11px] leading-relaxed">{ex.common_mistakes}</p>
                      </div>
                    )}
                    {ex.tips && (
                      <div>
                        <span className="font-bold text-amber-600 flex items-center gap-1 mb-1">
                          <Lightbulb className="h-3 w-3" /> Pro Tip
                        </span>
                        <p className="text-muted-foreground text-[11px] leading-relaxed">{ex.tips}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-4 flex justify-end">
            <Button
              className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md flex items-center space-x-1.5"
              onClick={() => setActiveTab("lab")}
            >
              <span>Launch Hands-on Lab</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </div>
          <div id="bottom-detector-examples" data-tab-id="examples" className="h-1 w-full" />
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB: HANDS-ON LAB (side-by-side split)                       */}
      {/* ============================================================ */}
      {activeTab === "lab" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start animate-fade-in">
          {/* Left Column: Lab instructions Stepper */}
          <div className="lg:col-span-5 space-y-6">
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

                {/* Syntax Example */}
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">Example Command Syntax</span>
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
                    Start a temporary Linux container shell process to execute task operations. Terminal sessions persist in the background.
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

      {/* ============================================================ */}
      {/* TAB: PRACTICE EXERCISES (standalone, full-width, with terminal) */}
      {/* ============================================================ */}
      {activeTab === "exercises" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start animate-fade-in">
          {/* Left: Exercise List */}
          <div className="lg:col-span-5 space-y-5">
            <div className="space-y-1">
              <h2 className="text-base font-bold text-foreground">Practice Exercises</h2>
              <p className="text-xs text-muted-foreground">
                These are <strong>not validated</strong> — purely for practice. Use the terminal on the right.
              </p>
            </div>

            {/* Group by difficulty */}
            {DIFFICULTY_ORDER.filter((level) => groupedExercises[level]?.length > 0).map((level) => {
              const group = groupedExercises[level] || [];
              return (
                <div key={level} className="space-y-3">
                  <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border w-fit text-xs font-bold ${DIFFICULTY_COLORS[level] || "bg-muted text-muted-foreground border-border/50"}`}>
                    {DIFFICULTY_LABELS[level] || level}
                  </div>

                  <div className="space-y-3">
                    {group.map((ex: any, idx: number) => {
                      const globalIdx = exercises.indexOf(ex);
                      return (
                        <div key={idx} className="p-4 border border-border/60 bg-card rounded-xl space-y-3">
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-xs font-semibold text-foreground leading-relaxed">{ex.problem}</p>
                          </div>

                          {ex.objective && (
                            <p className="text-[11px] text-muted-foreground leading-relaxed">
                              <strong className="text-foreground/70">Objective:</strong> {ex.objective}
                            </p>
                          )}

                          {ex.expected_result && (
                            <p className="text-[11px] text-muted-foreground">
                              <strong className="text-foreground/70">Expected:</strong> {ex.expected_result}
                            </p>
                          )}

                          {/* Collapsible hint */}
                          <div>
                            <button
                              type="button"
                              onClick={() =>
                                setOpenExerciseHints((prev) => ({ ...prev, [globalIdx]: !prev[globalIdx] }))
                              }
                              className="text-xs font-semibold text-primary hover:underline flex items-center space-x-1 cursor-pointer"
                            >
                              <HelpCircle className="h-3.5 w-3.5" />
                              <span>{openExerciseHints[globalIdx] ? "Hide Hint" : "Show Hint"}</span>
                            </button>
                            {openExerciseHints[globalIdx] && (
                              <p className="text-xs font-mono bg-amber-500/5 text-amber-600 border border-amber-500/20 p-2.5 rounded mt-2 leading-relaxed">
                                {ex.hint}
                              </p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}

            <Button
              className="w-full bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-md py-2 flex items-center justify-center space-x-1.5"
              onClick={() => setActiveTab("quiz")}
            >
              <span>Continue to Module Quiz</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
            <div id="bottom-detector-exercises" data-tab-id="exercises" className="h-1 w-full" />
          </div>

          {/* Right: Terminal */}
          <div className="lg:col-span-7 space-y-4">
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-foreground">Practice Terminal</h3>
              <p className="text-xs text-muted-foreground">Use this sandbox to try out the exercises above.</p>
            </div>

            {isLoadingSession ? (
              <div className="rounded-xl border border-border bg-card p-12 text-center animate-pulse">
                <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">Checking active session...</p>
              </div>
            ) : !session ? (
              <div className="rounded-xl border border-border bg-card p-8 text-center space-y-6">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 border border-primary/20">
                  <TerminalIcon className="h-6 w-6 text-primary" />
                </div>
                <div className="space-y-2 max-w-sm mx-auto">
                  <h2 className="text-base font-black text-foreground">Practice Sandbox</h2>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Launch a Linux container to practice exercises freely.
                  </p>
                </div>
                <Button
                  disabled={launchMutation.isPending}
                  onClick={() => launchMutation.mutate()}
                  className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl px-6 py-2.5"
                >
                  {launchMutation.isPending ? "Spawning..." : "Launch Practice Terminal"}
                </Button>
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-card overflow-hidden shadow-md flex flex-col h-[65vh]">
                <div className="bg-[#18141F] border-b border-[#2E2838] px-4 py-3 flex justify-between items-center shrink-0">
                  <div className="flex items-center space-x-2">
                    <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[10px] font-extrabold text-white uppercase tracking-widest">
                      Practice Terminal (Active)
                    </span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => stopMutation.mutate(session.id)}
                    disabled={stopMutation.isPending}
                    className="h-7 text-[10px] font-bold border-red-500/20 text-red-500 hover:bg-red-500/10 rounded"
                  >
                    {stopMutation.isPending ? "Stopping..." : (
                      <>
                        <StopCircle className="h-3.5 w-3.5 mr-1" />
                        <span>Terminate</span>
                      </>
                    )}
                  </Button>
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

      {/* ============================================================ */}
      {/* TAB: MODULE QUIZ                                              */}
      {/* ============================================================ */}
      {activeTab === "quiz" && (
        <div className="max-w-4xl space-y-6 animate-fade-in">
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground">Module Quiz</h2>
            <p className="text-xs text-muted-foreground">
              {quiz.length} questions — you need <strong>{Math.ceil(quiz.length * 0.8)}/{quiz.length}</strong> to pass.
              Read each question carefully before answering.
            </p>
          </div>

          <form onSubmit={handleQuizSubmit} className="space-y-5">
            {quiz.map((q: any, idx: number) => {
              const isSelected = (opt: string) => quizAnswers[idx] === opt;
              const isCorrect = quizAnswers[idx] === q.answer;
              return (
                <div key={idx} className="border border-border bg-card rounded-xl overflow-hidden shadow-sm">
                  {/* Question header */}
                  <div className="bg-muted/30 border-b border-border/40 px-5 py-3 flex items-start gap-3">
                    <span className="text-xs font-black text-primary bg-primary/10 border border-primary/20 h-5 w-5 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-foreground leading-relaxed">{q.question}</p>
                      {q.type && (
                        <span className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5 block">{q.type}</span>
                      )}
                    </div>
                  </div>

                  <div className="p-5 space-y-3">
                    <div className="grid grid-cols-1 gap-2">
                      {q.options.map((opt: string) => {
                        const selected = isSelected(opt);
                        const showResult = quizSubmitted;
                        const isCorrectOpt = opt === q.answer;
                        return (
                          <label
                            key={opt}
                            className={`flex items-center space-x-3 p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                              showResult
                                ? isCorrectOpt
                                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-700"
                                  : selected && !isCorrectOpt
                                  ? "bg-red-500/10 border-red-500/30 text-red-600"
                                  : "bg-muted/10 border-border/40 text-muted-foreground"
                                : selected
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
                            <span className="flex-1">{opt}</span>
                            {showResult && isCorrectOpt && (
                              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                            )}
                            {showResult && selected && !isCorrectOpt && (
                              <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
                            )}
                          </label>
                        );
                      })}
                    </div>

                    {/* Post-submit explanation */}
                    {quizSubmitted && (
                      <div className="p-4 bg-muted/40 rounded-lg text-xs space-y-2 border border-border/30">
                        <p className="text-foreground/90 font-medium leading-relaxed">
                          <span className="font-bold text-foreground">Explanation: </span>
                          {q.explanation}
                        </p>
                        {q.incorrect_explanations && (
                          <div className="text-[11px] text-muted-foreground pt-1 border-t border-border/20 space-y-1">
                            <span className="font-bold block text-foreground/70 mb-0.5">Why other options are wrong:</span>
                            {Object.entries(q.incorrect_explanations).map(([opt, desc]: any) => (
                              <p key={opt}>
                                <span className="font-semibold text-foreground/60 font-mono bg-muted px-1 rounded">{opt}:</span>{" "}
                                {desc}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {!quizSubmitted ? (
              <div className="pt-4 border-t border-border/40 flex items-center justify-between">
                <p className="text-xs text-muted-foreground">
                  {Object.keys(quizAnswers).length} of {quiz.length} answered
                </p>
                <Button
                  type="submit"
                  disabled={Object.keys(quizAnswers).length < quiz.length}
                  className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl px-8 py-2.5 shadow-sm cursor-pointer"
                >
                  Submit Quiz
                </Button>
              </div>
            ) : (
              <div className="pt-6 border-t border-border/40 space-y-4 animate-fade-in text-center">
                {quizPassed ? (
                  <div className="p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-xl inline-block max-w-sm mx-auto">
                    <div className="text-3xl mb-2">🏆</div>
                    <h4 className="text-sm font-bold text-emerald-600">Quiz Passed!</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      You scored <span className="font-bold text-foreground">{quizScore}</span> /{" "}
                      <span className="font-bold text-foreground">{quiz.length}</span> — well done!
                    </p>
                  </div>
                ) : (
                  <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-xl inline-block max-w-sm mx-auto">
                    <div className="text-3xl mb-2">📝</div>
                    <h4 className="text-sm font-bold text-red-500">Not Quite</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      You scored <span className="font-bold text-foreground">{quizScore}</span> /{" "}
                      <span className="font-bold text-foreground">{quiz.length}</span>. Need{" "}
                      <span className="font-bold text-primary">{Math.ceil(quiz.length * 0.8)}/{quiz.length}</span> to pass.
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
      )}

      {/* ============================================================ */}
      {/* TAB: RESOURCES                                                */}
      {/* ============================================================ */}
      {activeTab === "resources" && (
        <div className="max-w-5xl space-y-6 animate-fade-in">
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground">Resources & References</h2>
            <p className="text-xs text-muted-foreground">
              Official documentation, cheat sheets, command references, and further reading.
            </p>
          </div>

          <div className="space-y-6">
            {/* Module Summary */}
            <div className="p-5 bg-muted/30 border border-border/50 rounded-xl space-y-2">
              <span className="font-bold text-primary block uppercase tracking-wider text-[10px]">Module Summary</span>
              <p className="text-sm text-foreground/80 leading-relaxed">
                {details.resources?.summary || "Review the key concepts covered in this module."}
              </p>
            </div>

            {/* Quick Links Grid */}
            {(details.resources?.links || details.resources?.documentation || details.resources?.external_resources) && (
              <div className="space-y-3">
                <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">
                  Official Documentation & Links
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {[
                    ...(details.resources?.links || []),
                    ...(details.resources?.documentation || []),
                    ...(details.resources?.external_resources || []),
                  ].map((link: any, idx: number) => (
                    <a
                      key={idx}
                      href={link.url}
                      target="_blank"
                      rel="noreferrer"
                      className="group flex items-start gap-3 p-4 bg-card border border-border/60 rounded-xl hover:border-primary/40 hover:bg-primary/5 transition-all"
                    >
                      <div className="h-8 w-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                        <Globe className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-bold text-foreground group-hover:text-primary transition-colors block leading-tight">
                          {link.title}
                        </span>
                        {link.description && (
                          <p className="text-[10px] text-muted-foreground mt-0.5 leading-relaxed">{link.description}</p>
                        )}
                      </div>
                      <ExternalLink className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5 group-hover:text-primary transition-colors" />
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Cheat Sheet */}
            {details.resources?.cheat_sheet && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">
                    Quick Commands Cheat Sheet
                  </span>
                  <button
                    onClick={() => handleCopyCheatSheet(details.resources.cheat_sheet)}
                    className="flex items-center gap-1.5 text-[10px] font-bold text-primary hover:text-primary/80 transition-colors cursor-pointer"
                  >
                    <Copy className="h-3 w-3" />
                    {cheatCopied ? "Copied!" : "Copy All"}
                  </button>
                </div>
                <pre className="p-5 bg-[#1C1824] text-[#EFEBF4] rounded-xl border border-border/40 font-mono text-xs overflow-x-auto leading-relaxed">
                  {details.resources.cheat_sheet}
                </pre>
              </div>
            )}

            {/* Command Reference Table */}
            {details.resources?.commands_table && (
              <div className="space-y-2">
                <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">
                  Command Reference Table
                </span>
                <div className="overflow-x-auto border border-border/60 rounded-xl">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-muted/80 text-foreground font-bold border-b border-border/50">
                        <th className="p-3 text-[10px] uppercase">Command</th>
                        <th className="p-3 text-[10px] uppercase">Syntax</th>
                        <th className="p-3 text-[10px] uppercase">Description</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/40">
                      {details.resources.commands_table.map((row: any, i: number) => (
                        <tr key={i} className={i % 2 === 0 ? "bg-transparent" : "bg-muted/10"}>
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {details.resources?.revision_notes && (
                <div className="space-y-2">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Revision Notes</span>
                  <ul className="space-y-2">
                    {details.resources.revision_notes.map((note: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-muted-foreground">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{note}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {details.resources?.best_practices && (
                <div className="space-y-2">
                  <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Best Practices</span>
                  <ul className="space-y-2">
                    {details.resources.best_practices.map((practice: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-muted-foreground">
                        <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{practice}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Common Mistakes */}
            {details.resources?.beginner_mistakes && (
              <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-xl space-y-2">
                <span className="font-bold text-red-500 block uppercase tracking-wider text-[10px]">Common Mistakes to Avoid</span>
                <ul className="space-y-2">
                  {details.resources.beginner_mistakes.map((mistake: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-xs text-muted-foreground">
                      <AlertCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                      <span>{mistake}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Interview Questions */}
            {details.resources?.interview_questions && (
              <div className="space-y-3">
                <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">
                  Interview Questions
                </span>
                <div className="space-y-3">
                  {details.resources.interview_questions.map((faq: any, i: number) => (
                    <div key={i} className="p-4 bg-muted/20 border border-border/50 rounded-xl space-y-1">
                      <p className="text-xs font-bold text-foreground">Q: {faq.question}</p>
                      <p className="text-xs text-muted-foreground leading-relaxed">A: {faq.answer}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Books */}
            {details.resources?.books && details.resources.books.length > 0 && (
              <div className="space-y-2">
                <span className="font-bold text-foreground block uppercase tracking-wider text-[10px]">Further Reading</span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {details.resources.books.map((book: any, idx: number) => (
                    <div key={idx} className="p-4 bg-card border border-border/60 rounded-xl flex items-start gap-3">
                      <div className="h-8 w-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
                        <FileText className="h-4 w-4 text-amber-600" />
                      </div>
                      <div>
                        <span className="text-xs font-bold text-foreground block">{book.title}</span>
                        {book.description && (
                          <p className="text-[10px] text-muted-foreground mt-0.5 leading-relaxed">{book.description}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-6 border-t border-border/40 text-center">
            <Button
              onClick={handleFinishModule}
              className="bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl px-8 py-2.5 cursor-pointer"
            >
              Finish Module
            </Button>
          </div>
        </div>
      )}

      {/* Finish Module Toast */}
      {showFinishToast && (
        <div className="fixed bottom-6 right-6 z-50 animate-fade-in max-w-sm w-full">
          <div className="bg-card border border-border rounded-xl shadow-2xl p-4 flex items-start gap-3">
            <div className="shrink-0 h-8 w-8 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-lg">
              ℹ️
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-foreground mb-0.5">Complete All Content First</p>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Please complete Overview, Key Concepts, Examples, Lab tasks, Exercises, and pass the Quiz before finishing this module.
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
