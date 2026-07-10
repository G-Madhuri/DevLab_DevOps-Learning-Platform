"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { labService } from "@/services/lab.service";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Search,
  SlidersHorizontal,
  Clock,
  ExternalLink,
  BookOpen,
  HelpCircle,
  Terminal,
  Container,
  Layers,
  Cpu,
  Globe,
  Settings,
  GitBranch,
  Play,
  BarChart,
  Activity,
  HardDrive,
} from "lucide-react";

export default function LabsCatalogPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [difficulty, setDifficulty] = useState("All");
  const [sort, setSort] = useState("alphabetical");

  // Fetch labs list using React Query
  const { data, isLoading } = useQuery({
    queryKey: ["labs", search, category, difficulty, sort],
    queryFn: () =>
      labService.listLabs({
        search: search || undefined,
        category: category === "All" ? undefined : category,
        difficulty: difficulty === "All" ? undefined : difficulty,
        sort_by: sort,
      }),
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

  // Helper to map categories to React Icons dynamically
  const getCategoryIcon = (cat: string) => {
    switch (cat.toLowerCase()) {
      case "linux":
        return <Terminal className="h-4 w-4" />;
      case "docker":
        return <Container className="h-4 w-4" />;
      case "kubernetes":
        return <Layers className="h-4 w-4" />;
      case "terraform":
        return <Cpu className="h-4 w-4" />;
      case "aws":
        return <Globe className="h-4 w-4" />;
      case "azure":
        return <HardDrive className="h-4 w-4" />;
      case "jenkins":
        return <Settings className="h-4 w-4" />;
      case "ansible":
        return <BookOpen className="h-4 w-4" />;
      case "git":
        return <GitBranch className="h-4 w-4" />;
      case "github actions":
        return <Play className="h-4 w-4" />;
      case "monitoring":
        return <BarChart className="h-4 w-4" />;
      case "observability":
        return <Activity className="h-4 w-4" />;
      default:
        return <HelpCircle className="h-4 w-4" />;
    }
  };

  // Helper to get difficulty badges classes
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

  // Simulated tags generator based on labs title & categories to make cards pop
  const generateMockSkills = (title: string, cat: string) => {
    const defaultSkills = [cat, "DevOps"];
    if (title.toLowerCase().includes("basics") || title.toLowerCase().includes("intro")) {
      return [...defaultSkills, "CLI", "Foundations"];
    }
    if (title.toLowerCase().includes("pipeline") || title.toLowerCase().includes("ci")) {
      return [...defaultSkills, "Automation", "CI/CD"];
    }
    if (title.toLowerCase().includes("state") || title.toLowerCase().includes("store")) {
      return [...defaultSkills, "Backend", "Storage"];
    }
    if (title.toLowerCase().includes("advanced") || title.toLowerCase().includes("deep")) {
      return [...defaultSkills, "Expert", "Security"];
    }
    return [...defaultSkills, "Configuration"];
  };

  return (
    <DashboardShell>
      {/* Page Header */}
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Interactive Labs</h1>
        <p className="text-sm text-muted-foreground">
          Select an exercise topic below to read details. Environments will become deployable in Phase 3.
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
              {cat !== "All" && getCategoryIcon(cat)}
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
            placeholder="Search labs by title, category, or descriptions..."
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
              <option value="alphabetical">Alphabetical</option>
              <option value="difficulty">Difficulty</option>
              <option value="duration">Estimated Time</option>
            </select>
          </div>
        </div>
      </div>

      {/* Skeletons Loader */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="border border-border bg-card/60 rounded-xl p-5 space-y-4 animate-pulse"
            >
              <div className="flex justify-between items-center">
                <div className="h-5 bg-muted rounded w-20" />
                <div className="h-5 bg-muted rounded w-16" />
              </div>
              <div className="h-6 bg-muted rounded w-2/3" />
              <div className="space-y-2">
                <div className="h-4 bg-muted rounded w-full" />
                <div className="h-4 bg-muted rounded w-5/6" />
              </div>
              <div className="flex gap-2">
                <div className="h-5 bg-muted rounded-full w-12" />
                <div className="h-5 bg-muted rounded-full w-16" />
              </div>
              <div className="flex gap-4 pt-2">
                <div className="h-9 bg-muted rounded w-24" />
                <div className="h-9 bg-muted rounded w-24" />
              </div>
            </div>
          ))}
        </div>
      ) : data?.labs.length === 0 ? (
        /* Empty State */
        <div className="rounded-xl border border-border bg-card p-12 text-center shadow-sm">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted border border-border">
            <Search className="h-5 w-5 text-muted-foreground" />
          </div>
          <h3 className="mt-4 text-base font-bold text-foreground">No labs match search</h3>
          <p className="mt-1 text-xs text-muted-foreground max-w-sm mx-auto leading-relaxed">
            We couldn&apos;t find any labs matching your filters. Try removing keywords or clearing search fields.
          </p>
          <Button
            variant="outline"
            className="mt-4 rounded-md text-xs font-semibold"
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
        /* Labs Grid List */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {data?.labs.map((lab) => (
            <div
              key={lab.id}
              className="flex flex-col justify-between border border-border bg-card rounded-xl p-5 hover:shadow-md hover:border-primary/30 transition-all duration-200"
            >
              <div className="space-y-3">
                {/* Tag Header */}
                <div className="flex justify-between items-center text-xs">
                  <span className="inline-flex items-center space-x-1.5 font-bold text-primary bg-primary/10 border border-primary/20 px-2.5 py-0.5 rounded-full uppercase text-[10px]">
                    {getCategoryIcon(lab.category)}
                    <span>{lab.category}</span>
                  </span>
                  <span
                    className={`px-2 py-0.5 border rounded-full text-[10px] font-bold uppercase tracking-wider ${getDifficultyStyles(
                      lab.difficulty
                    )}`}
                  >
                    {lab.difficulty}
                  </span>
                </div>

                {/* Title */}
                <h3 className="text-base font-bold text-foreground leading-snug tracking-tight">
                  {lab.title}
                </h3>

                {/* Description */}
                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                  {lab.description}
                </p>

                {/* Simulated Tags */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {generateMockSkills(lab.title, lab.category).map((skill, index) => (
                    <span
                      key={index}
                      className="text-[10px] text-muted-foreground bg-muted/60 border border-border/50 px-1.5 py-0.5 rounded"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Toolbar Footer */}
              <div className="flex items-center justify-between pt-4 mt-4 border-t border-border/40">
                <div className="flex items-center text-xs text-muted-foreground">
                  <Clock className="h-3.5 w-3.5 mr-1" />
                  <span>{lab.estimated_time}</span>
                </div>

                <div className="flex items-center space-x-2">
                  <Link href={`/labs/${lab.slug}`}>
                    <Button variant="ghost" size="sm" className="text-xs font-semibold rounded-md">
                      <span className="flex items-center space-x-1">
                        <span>Details</span>
                        <ExternalLink className="h-3.5 w-3.5" />
                      </span>
                    </Button>
                  </Link>

                  <Button
                    size="sm"
                    disabled
                    className="bg-primary/50 text-primary-foreground/70 cursor-not-allowed text-xs font-semibold rounded-md shadow-sm border border-transparent"
                  >
                    Coming Soon
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardShell>
  );
}
