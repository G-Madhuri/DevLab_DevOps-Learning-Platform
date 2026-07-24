"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { labService } from "@/services/lab.service";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Search,
  SlidersHorizontal,
  Clock,
  BookOpen,
  HelpCircle,
  Terminal,
  Container,
  Layers,
  Cpu,
  Globe,
  Settings as SettingsIcon,
  GitBranch,
  Play,
  BarChart,
  Activity,
  HardDrive,
  ChevronDown,
  ChevronUp,
  Award,
  CheckCircle2,
  Lock,
} from "lucide-react";

export default function LabsCatalogPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [difficulty, setDifficulty] = useState("All");
  const [sort, setSort] = useState("default");

  const [expandedAcademies, setExpandedAcademies] = useState<Record<string, boolean>>({
    linux: true, // Expand Linux Academy by default
  });

  // Query academies list using React Query
  const { data: academies = [], isLoading } = useQuery({
    queryKey: ["academies_list"],
    queryFn: () => labService.listAcademies(),
  });

  // Generate certificate mutation
  const generateCertMutation = useMutation({
    onSuccess: (res) => {
      alert(res.message);
      queryClient.invalidateQueries({ queryKey: ["academies_list"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to generate certificate.");
    },
    mutationFn: (academyId: string) => labService.generateCertificate(academyId),
  });

  const generateCourseCertMutation = useMutation({
    onSuccess: (res) => {
      alert(res.message);
      queryClient.invalidateQueries({ queryKey: ["academies_list"] });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to generate course certificate.");
    },
    mutationFn: (courseSlug: string) => labService.generateCourseCertificate(courseSlug),
  });

  const categories = [
    "All",
    "Linux",
    "Docker",
    "Kubernetes",
    "Terraform",
    "AWS",
    "Azure",
    "Jenkins",
    "Ansible",
    "Git",
    "GitHub Actions",
    "Monitoring",
    "Observability",
  ];

  const getAcademyIcon = (iconName: string) => {
    switch (iconName.toLowerCase()) {
      case "terminal":
        return <Terminal className="h-5 w-5 text-primary" />;
      case "box":
        return <Container className="h-5 w-5 text-primary" />;
      case "layers":
        return <Layers className="h-5 w-5 text-primary" />;
      case "cpu":
        return <Cpu className="h-5 w-5 text-primary" />;
      case "globe":
        return <Globe className="h-5 w-5 text-primary" />;
      case "hard-drive":
        return <HardDrive className="h-5 w-5 text-primary" />;
      case "settings":
        return <SettingsIcon className="h-5 w-5 text-primary" />;
      case "book-open":
        return <BookOpen className="h-5 w-5 text-primary" />;
      case "git-branch":
        return <GitBranch className="h-5 w-5 text-primary" />;
      case "play":
        return <Play className="h-5 w-5 text-primary" />;
      case "bar-chart":
        return <BarChart className="h-5 w-5 text-primary" />;
      case "activity":
        return <Activity className="h-5 w-5 text-primary" />;
      default:
        return <HelpCircle className="h-5 w-5 text-primary" />;
    }
  };

  const getDifficultyStyles = (diff: string) => {
    switch (diff.toLowerCase()) {
      case "beginner":
        return "bg-emerald-500/10 text-emerald-600 border-emerald-500/20";
      case "intermediate":
        return "bg-amber-500/10 text-amber-600 border-amber-500/20";
      case "advanced":
        return "bg-red-500/10 text-red-600 border-red-500/20";
      default:
        return "bg-slate-500/10 text-slate-600 border-slate-500/20";
    }
  };

  const toggleAcademy = (id: string) => {
    setExpandedAcademies((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const formatDuration = (totalMinutes: number) => {
    const hrs = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    if (hrs > 0) {
      return `${hrs} hr${hrs > 1 ? "s" : ""} ${mins > 0 ? `${mins} min${mins > 1 ? "s" : ""}` : ""}`.trim();
    }
    return `${totalMinutes} mins`;
  };

  // Filter & Sort academies client-side based on toolbar controls
  const filteredAndSortedAcademies = academies
    .filter((academy) => {
      // 1. Search Query filter
      const query = search.toLowerCase();
      const matchesTitle = academy.title.toLowerCase().includes(query);
      const matchesDesc = academy.description.toLowerCase().includes(query);
      const matchesCourses = academy.courses.some(
        (c: any) =>
          c.title.toLowerCase().includes(query) ||
          c.description.toLowerCase().includes(query)
      );
      if (search && !matchesTitle && !matchesDesc && !matchesCourses) {
        return false;
      }

      // 2. Category filter
      if (category !== "All") {
        const categorySlug = category.toLowerCase().replace(" ", "-");
        const matchesCat =
          academy.id === categorySlug ||
          academy.title.toLowerCase().includes(category.toLowerCase());
        if (!matchesCat) return false;
      }

      // 3. Difficulty Level filter
      if (difficulty !== "All") {
        const matchesDiff = academy.difficulty.toLowerCase() === difficulty.toLowerCase();
        if (!matchesDiff) return false;
      }

      return true;
    })
    .sort((a, b) => {
      // 4. Sort calculations
      if (sort === "default") {
        const roadmapOrder = [
          "linux", "git", "docker", "cicd", "github-actions", "jenkins", "ansible", "terraform", "aws", "azure", "kubernetes", "monitoring", "observability"
        ];
        return roadmapOrder.indexOf(a.id) - roadmapOrder.indexOf(b.id);
      }
      if (sort === "alphabetical") {
        return a.title.localeCompare(b.title);
      }
      if (sort === "difficulty") {
        const diffWeight = (d: string) => {
          const l = d.toLowerCase();
          if (l === "beginner") return 1;
          if (l === "intermediate") return 2;
          return 3;
        };
        return diffWeight(a.difficulty) - diffWeight(b.difficulty);
      }
      if (sort === "duration") {
        const getDuration = (ac: any) =>
          ac.courses.reduce((sum: number, c: any) => sum + (parseInt(c.duration) || 30), 0);
        return getDuration(b) - getDuration(a); // Sort descending (longer duration first)
      }
      return 0;
    });

  return (
    <DashboardShell>
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">DevOps Courses</h1>
        <p className="text-sm text-muted-foreground">
          Choose a specialized pathway, complete interactive browser-based terminal sandboxes, and unlock completion certificates.
        </p>
      </div>

      {/* Categories Scroller */}
      <div className="flex overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 gap-2 scrollbar-none">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold border shrink-0 transition-all cursor-pointer ${
              category === cat
                ? "bg-primary border-primary text-primary-foreground shadow-sm font-bold"
                : "bg-card border-border text-muted-foreground hover:text-foreground hover:bg-muted"
            }`}
          >
            <span className="flex items-center space-x-1.5">
              {cat !== "All" && getAcademyIcon(cat === "Git" ? "git-branch" : cat === "Docker" ? "box" : cat)}
              <span>{cat}</span>
            </span>
          </button>
        ))}
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col md:flex-row gap-4 items-center bg-card border border-border p-4 rounded-xl shadow-sm">
        {/* Search */}
        <div className="relative w-full md:flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search academies or courses by title and description..."
            className="pl-9 w-full bg-background border border-input rounded-md"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Filters */}
        <div className="flex w-full md:w-auto items-center gap-2">
          {/* Difficulty Filter */}
          <div className="flex items-center space-x-2 bg-background border border-input px-3 py-1.5 rounded-md min-w-[140px]">
            <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="bg-transparent border-none text-xs font-semibold focus:outline-none w-full cursor-pointer text-foreground"
            >
              <option value="All">All Levels</option>
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
            </select>
          </div>

          {/* Sort Filter */}
          <div className="flex items-center space-x-2 bg-background border border-input px-3 py-1.5 rounded-md min-w-[140px]">
            <SlidersHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="bg-transparent border-none text-xs font-semibold focus:outline-none w-full cursor-pointer text-foreground"
            >
              <option value="default">Default Order</option>
              <option value="alphabetical">Alphabetical</option>
              <option value="difficulty">Difficulty</option>
              <option value="duration">Estimated Time</option>
            </select>
          </div>
        </div>
      </div>

      {/* Loader */}
      {isLoading ? (
        <div className="space-y-6">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="border border-border bg-card/60 rounded-xl p-6 space-y-4 animate-pulse"
            >
              <div className="flex items-center space-x-4">
                <div className="h-12 w-12 bg-muted rounded-lg" />
                <div className="space-y-2 flex-1">
                  <div className="h-5 bg-muted rounded w-1/4" />
                  <div className="h-4 bg-muted rounded w-2/3" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : filteredAndSortedAcademies.length === 0 ? (
        <div className="rounded-xl border border-border bg-card p-12 text-center shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted border border-border">
            <Search className="h-5 w-5 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-base font-bold text-foreground">No academies match search</h3>
          <p className="mt-1 text-xs text-muted-foreground max-w-sm mx-auto leading-relaxed">
            We couldn&apos;t find any academies matching your filters. Try clearing search fields or filters.
          </p>
          <Button
            variant="outline"
            className="mt-4 rounded-xl text-xs font-semibold"
            onClick={() => {
              setSearch("");
              setCategory("All");
              setDifficulty("All");
            }}
          >
            Clear Filters
          </Button>
        </div>
      ) : (
        /* Academies Stack */
        <div className="space-y-6">
          {filteredAndSortedAcademies.map((academy) => {
            const isExpanded = !!expandedAcademies[academy.id];
            const coursesCount = academy.courses.length;
            // Calculate total time
            const totalDurationMinutes = academy.courses.reduce((acc: number, c: any) => {
              const minutes = parseInt(c.duration) || 30;
              return acc + minutes;
            }, 0);

            return (
              <div
                key={academy.id}
                className="border border-border bg-card rounded-xl shadow-sm overflow-hidden transition-all duration-200"
              >
                {/* Academy Header Card */}
                <div className="p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-card hover:bg-muted/10 transition-colors">
                  <div className="flex items-start space-x-4 flex-1">
                    <div className="p-3 bg-primary/10 rounded-xl border border-primary/20 shrink-0">
                      {getAcademyIcon(academy.icon)}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <h2 className="text-lg font-bold text-foreground tracking-tight">
                          {academy.title}
                        </h2>
                        <span
                          className={`px-2 py-0.5 border rounded-full text-[9px] font-bold uppercase tracking-wider ${getDifficultyStyles(
                            academy.difficulty
                          )}`}
                        >
                          {academy.difficulty}
                        </span>
                        {academy.coming_soon && (
                          <span className="px-2 py-0.5 border border-muted bg-muted/50 text-muted-foreground rounded-full text-[9px] font-bold uppercase tracking-wider">
                            Locked
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed max-w-2xl">
                        {academy.description}
                      </p>
                    </div>
                  </div>

                  {/* Summary metrics / Progress */}
                  <div className="flex flex-col md:flex-row items-stretch md:items-center gap-4 w-full md:w-auto text-xs shrink-0">
                    <div className="flex items-center space-x-4 text-muted-foreground border-border/40 md:border-r pr-4">
                      <div className="space-y-0.5">
                        <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">Courses</p>
                        <p className="font-bold text-foreground">{coursesCount} modules</p>
                      </div>
                      <div className="space-y-0.5">
                        <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider">Duration</p>
                        <p className="font-bold text-foreground">{formatDuration(totalDurationMinutes)}</p>
                      </div>
                    </div>

                    {/* Progress details */}
                    {!academy.coming_soon && (
                      <div className="space-y-1 w-full md:w-32">
                        <div className="flex justify-between font-bold text-foreground text-[10px]">
                          <span>PROGRESS</span>
                          <span>{academy.progress}%</span>
                        </div>
                        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden border border-border/50">
                          <div
                            className="h-full bg-primary transition-all duration-300"
                            style={{ width: `${academy.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => toggleAcademy(academy.id)}
                      className="rounded-xl flex items-center space-x-1.5 py-2 cursor-pointer border border-border bg-card"
                    >
                      <span>{isExpanded ? "Collapse" : "Explore"}</span>
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                {/* Expanded Course Listing Section */}
                {isExpanded && (
                  <div className="border-t border-border/50 bg-muted/10 p-6 space-y-4">
                    {academy.coming_soon ? (
                      <div className="text-center py-6">
                        <Lock className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                        <h4 className="text-sm font-bold text-foreground">Academy Coming Soon</h4>
                        <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                          Our curriculum team is currently writing courses and configurations for this Academy. Stay tuned!
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {academy.courses.map((course: any, idx: number) => {
                          const isCompleted = course.percentage === 100;
                          return (
                            <div
                              key={course.slug}
                              className={`flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 rounded-xl border bg-card transition-all duration-150 ${
                                course.is_capstone
                                  ? "border-indigo-500/30 hover:border-indigo-500/50 bg-indigo-500/[0.01]"
                                  : "border-border hover:border-primary/20"
                              }`}
                            >
                              <div className="space-y-1.5 flex-1 pr-4">
                                <div className="flex items-center space-x-2">
                                  <span className="text-xs font-bold text-muted-foreground shrink-0">
                                    {String(idx + 1).padStart(2, "0")}.
                                  </span>
                                  <h3 className="text-sm font-bold text-foreground tracking-tight">
                                    {course.title}
                                  </h3>
                                  {course.is_capstone && (
                                    <span className="bg-indigo-500/10 text-indigo-600 border border-indigo-500/20 px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider">
                                      Capstone
                                    </span>
                                  )}
                                  {isCompleted && (
                                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                                  )}
                                </div>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                  {course.description}
                                </p>
                                <div className="flex items-center space-x-3 text-[10px] text-muted-foreground">
                                  <span className="flex items-center">
                                    <Clock className="h-3 w-3 mr-1" />
                                    {course.duration}
                                  </span>
                                  <span className="capitalize">{course.difficulty}</span>
                                </div>
                              </div>

                              {/* Progress bar and launching actions */}
                              <div className="flex items-center space-x-4 w-full sm:w-auto mt-4 sm:mt-0 shrink-0 border-t sm:border-t-0 border-border/40 pt-3 sm:pt-0">
                                <div className="space-y-1 w-24">
                                  <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden border border-border/50">
                                    <div
                                      className="h-full bg-primary transition-all duration-200"
                                      style={{ width: `${course.percentage}%` }}
                                    />
                                  </div>
                                </div>

                                 {isCompleted ? (
                                  <Button
                                    size="sm"
                                    onClick={() => generateCourseCertMutation.mutate(course.slug)}
                                    disabled={generateCourseCertMutation.isPending}
                                    className="rounded-xl text-xs font-semibold bg-amber-500 hover:bg-amber-600 text-white cursor-pointer"
                                  >
                                    {generateCourseCertMutation.isPending ? "Claiming..." : "Claim Certificate"}
                                  </Button>
                                ) : null}

                                <Link href={`/labs/workspace/${course.slug}`}>
                                  <Button
                                    size="sm"
                                    className={`rounded-xl text-xs font-semibold ${
                                      isCompleted
                                        ? "bg-muted text-muted-foreground hover:bg-muted/80"
                                        : "bg-primary text-primary-foreground hover:bg-primary/95"
                                    }`}
                                  >
                                    Start Course
                                  </Button>
                                </Link>
                              </div>
                            </div>
                          );
                        })}

                        {/* Certificate Locked/Unlocked card slot */}
                        <div
                          className={`p-4 rounded-xl border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-card ${
                            academy.certificate_unlocked
                              ? "border-amber-500/30 bg-amber-500/[0.01]"
                              : "border-border/60 bg-card/60 opacity-90"
                          }`}
                        >
                          <div className="flex items-start space-x-3">
                            <div
                              className={`p-2 rounded-lg shrink-0 ${
                                academy.certificate_unlocked
                                  ? "bg-amber-500/10 border border-amber-500/20 text-amber-600"
                                  : "bg-muted text-muted-foreground border border-border/50"
                              }`}
                            >
                              <Award className="h-5 w-5" />
                            </div>
                            <div className="space-y-1">
                              <h4 className="text-sm font-bold text-foreground">
                                {academy.certificate_unlocked ? "🏆" : "🔒"}{" "}
                                {academy.title} Certificate
                              </h4>
                              <p className="text-xs text-muted-foreground leading-relaxed max-w-md">
                                {academy.certificate_unlocked
                                  ? `Congratulations! You have completed every course in ${academy.title}. You are ready to generate your certificate.`
                                  : `Complete all ${academy.title} courses and the Capstone to unlock this certificate.`}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2 w-full sm:w-auto shrink-0 border-t sm:border-t-0 border-border/40 pt-3 sm:pt-0">
                            {academy.certificate_unlocked ? (
                              <>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="rounded-xl text-xs border-amber-500/30 text-amber-600 hover:bg-amber-500/10 cursor-pointer"
                                  onClick={() => alert("Preview Certificate will display your final certification page.")}
                                >
                                  Preview Certificate
                                </Button>
                                <Button
                                  size="sm"
                                  className="rounded-xl text-xs bg-amber-600 hover:bg-amber-700 text-white cursor-pointer"
                                  disabled={generateCertMutation.isPending}
                                  onClick={() => generateCertMutation.mutate(academy.id)}
                                >
                                  {generateCertMutation.isPending ? "Generating..." : "Generate Certificate"}
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="rounded-xl text-xs border border-border cursor-pointer"
                                  onClick={() => alert("Downloading PDF...")}
                                >
                                  Download PDF
                                </Button>
                              </>
                            ) : (
                              <span className="text-xs font-semibold text-muted-foreground bg-muted border border-border/50 px-3 py-1.5 rounded-xl flex items-center space-x-1.5 select-none">
                                <Lock className="h-3 w-3" />
                                <span>Locked</span>
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </DashboardShell>
  );
}
