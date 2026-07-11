"use client";

import React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { labService } from "@/services/lab.service";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  Clock,
  Award,
  CheckCircle2,
  Lock,
  Play,
  Loader2,
  AlertCircle,
  BookOpen,
  Milestone,
} from "lucide-react";

export default function LearningPathDetailPage() {
  const params = useParams();
  const pathId = params.id as string;

  // Query learning path details dynamically
  const { data: path, isLoading } = useQuery({
    queryKey: ["learning_path_detail", pathId],
    queryFn: () => labService.getLearningPathDetail(pathId),
  });

  if (isLoading) {
    return (
      <DashboardShell>
        <div className="flex h-[50vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardShell>
    );
  }

  if (!path) {
    return (
      <DashboardShell>
        <div className="p-8 text-center bg-card border rounded-xl">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <h3 className="text-sm font-bold text-foreground">Path Not Found</h3>
          <p className="text-xs text-muted-foreground mt-1">We couldn&apos;t load the details for this Learning Path.</p>
        </div>
      </DashboardShell>
    );
  }

  const courses = path.courses_details || [];

  return (
    <DashboardShell>
      {/* Breadcrumb / Back Link */}
      <div className="flex items-center space-x-1.5 text-xs text-muted-foreground">
        <Link href="/learning-paths" className="hover:text-foreground transition-colors flex items-center gap-1">
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Pathways</span>
        </Link>
        <span className="text-muted-foreground/50">/</span>
        <span className="text-foreground font-semibold">{path.title} Roadmap</span>
      </div>

      {/* Path Header Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Side: Path Specs & Outcomes */}
        <div className="lg:col-span-4 space-y-6">
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-5">
            <div className="space-y-2">
              <h1 className="text-xl font-black text-foreground tracking-tight">{path.title}</h1>
              <p className="text-xs text-muted-foreground leading-relaxed">{path.description}</p>
            </div>

            {/* Path Metadata Items */}
            <div className="space-y-3 pt-3 border-t border-border/40 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground font-semibold">Difficulty Level:</span>
                <span className="font-bold text-primary capitalize">{path.difficulty}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground font-semibold">Estimated Time:</span>
                <span className="font-bold text-foreground flex items-center">
                  <Clock className="h-3.5 w-3.5 mr-1" />
                  {path.duration}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground font-semibold">Prerequisites:</span>
                <span className="font-bold text-foreground/80">{path.prerequisites[0]}</span>
              </div>
            </div>

            {/* Path Progress Tracker */}
            <div className="space-y-2 pt-3 border-t border-border/40">
              <div className="flex justify-between text-xs font-bold text-foreground">
                <span>PATHWAY PROGRESS</span>
                <span>{path.progress || 0}%</span>
              </div>
              <div className="h-2 w-full bg-muted rounded-full overflow-hidden border border-border/50">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                  style={{ width: `${path.progress || 0}%` }}
                />
              </div>
            </div>
          </div>

          {/* Career Objectives & Learning Outcomes Cards */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Career Objective</h3>
            <p className="text-xs text-foreground/80 leading-relaxed bg-muted/30 p-3 rounded-lg border border-border/40">
              {path.career_objective}
            </p>
          </div>

          <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Learning Outcomes</h3>
            <ul className="space-y-2 text-xs">
              {path.learning_outcomes.map((out: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                  <span className="text-muted-foreground leading-normal">{out}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Right Side: Timeline Roadmap */}
        <div className="lg:col-span-8 space-y-6">
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-muted-foreground mb-6">
              <Milestone className="h-4 w-4 text-primary" />
              <span>Curriculum Roadmap Progression</span>
            </div>

            {/* Timeline Tree Nodes */}
            <div className="relative pl-6 sm:pl-8 border-l-2 border-dashed border-border/60 ml-4 space-y-6">
              {courses.map((course: any, idx: number) => {
                const isCompleted = course.percentage === 100;
                const isInProgress = course.percentage > 0 && course.percentage < 100;

                return (
                  <div key={course.slug} className="relative group">
                    {/* Timeline Node Bullet */}
                    <div
                      className={`absolute -left-[35px] sm:-left-[43px] top-1 h-6 w-6 rounded-full border flex items-center justify-center shrink-0 shadow-sm transition-all duration-200 ${
                        isCompleted
                          ? "bg-emerald-500 border-emerald-500 text-white"
                          : isInProgress
                          ? "bg-primary border-primary text-primary-foreground scale-110"
                          : "bg-muted border-border/80 text-muted-foreground"
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : isInProgress ? (
                        <Play className="h-3 w-3 fill-current" />
                      ) : (
                        <span className="text-[10px] font-bold">{idx + 1}</span>
                      )}
                    </div>

                    {/* Course timeline card */}
                    <div
                      className={`p-5 rounded-xl border bg-card/60 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 transition-all duration-150 hover:border-primary/20 ${
                        isInProgress ? "border-primary/20 bg-primary/[0.01]" : "border-border"
                      }`}
                    >
                      <div className="space-y-1.5 flex-1 pr-4">
                        <div className="flex items-center space-x-2">
                          <h3 className="text-sm font-bold text-foreground tracking-tight">
                            {course.title}
                          </h3>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[8px] font-extrabold uppercase border ${
                              isCompleted
                                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-600"
                                : isInProgress
                                ? "bg-primary/10 border-primary/20 text-primary animate-pulse"
                                : "bg-muted text-muted-foreground border-border/50"
                            }`}
                          >
                            {course.status}
                          </span>
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

                      {/* Launch course button */}
                      <div className="shrink-0 w-full sm:w-auto">
                        <Link href={`/labs/workspace/${course.slug}`}>
                          <Button
                            size="sm"
                            className="w-full sm:w-auto rounded-xl text-xs font-bold bg-primary hover:bg-primary/95 text-primary-foreground cursor-pointer"
                          >
                            Open Course
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
