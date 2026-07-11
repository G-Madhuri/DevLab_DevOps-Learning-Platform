"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { labService } from "@/services/lab.service";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import {
  Compass,
  ArrowRight,
  Clock,
  Layers,
  CheckCircle2,
  Award,
  BookOpen,
  Boxes,
  Activity,
  Milestone,
  Loader2,
  AlertCircle,
} from "lucide-react";

export default function LearningPathsPage() {
  // Query career paths dynamically from config api
  const { data: paths = [], isLoading } = useQuery({
    queryKey: ["learning_paths_list"],
    queryFn: () => labService.listLearningPaths(),
  });

  const getPathTheme = (id: string) => {
    if (id.includes("kubernetes") || id.includes("container") || id.includes("sre") || id.includes("reliability")) {
      return {
        color: "from-indigo-500/20 via-indigo-500/5 to-transparent",
        accent: "text-indigo-500 border-indigo-500/20 bg-indigo-500/10",
      };
    }
    if (id.includes("cloud") || id.includes("aws") || id.includes("azure") || id.includes("monitoring")) {
      return {
        color: "from-amber-500/20 via-amber-500/5 to-transparent",
        accent: "text-amber-500 border-amber-500/20 bg-amber-500/10",
      };
    }
    if (id.includes("security") || id.includes("sec")) {
      return {
        color: "from-red-500/20 via-red-500/5 to-transparent",
        accent: "text-red-500 border-red-500/20 bg-red-500/10",
      };
    }
    return {
      color: "from-emerald-500/20 via-emerald-500/5 to-transparent",
      accent: "text-emerald-500 border-emerald-500/20 bg-emerald-500/10",
    };
  };

  return (
    <DashboardShell>
      {/* Page Header */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2 text-primary font-bold text-xs uppercase tracking-wider">
          <Milestone className="h-4 w-4" />
          <span>DevOps Pathways</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Learning Paths</h1>
        <p className="text-sm text-muted-foreground">
          Accelerate your DevOps career by following structured, curated roadmaps combining multiple course modules.
        </p>
      </div>

      {/* Loading Loader */}
      {isLoading ? (
        <div className="flex h-[30vh] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : paths.length === 0 ? (
        <div className="p-8 text-center bg-card border rounded-xl">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <h3 className="text-sm font-bold text-foreground">Pathways Configurations Not Loaded</h3>
          <p className="text-xs text-muted-foreground mt-1">Failed to read paths details from configurations files.</p>
        </div>
      ) : (
        /* Grid of Learning Paths */
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {paths.map((path) => {
            const theme = getPathTheme(path.id);
            return (
              <div
                key={path.id}
                className={`rounded-xl border border-border bg-gradient-to-b ${theme.color} p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition-all duration-200 hover:border-primary/20 text-left`}
              >
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span
                      className={`px-2 py-0.5 border rounded-full text-[9px] font-bold uppercase tracking-wider ${theme.accent}`}
                    >
                      {path.difficulty}
                    </span>
                    <span className="text-[10px] text-muted-foreground font-semibold flex items-center">
                      <Clock className="h-3.5 w-3.5 mr-1" />
                      {path.duration}
                    </span>
                  </div>

                  <div className="space-y-1">
                    <h2 className="text-base font-bold text-foreground tracking-tight">{path.title}</h2>
                    <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2 h-8">{path.description}</p>
                  </div>

                  {/* Progress Tracker */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-[10px] font-bold text-foreground">
                      <span>PATH PROGRESS</span>
                      <span>{path.progress || 0}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden border border-border/50">
                      <div
                        className="h-full bg-primary transition-all duration-300"
                        style={{ width: `${path.progress || 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Courses list preview */}
                  <div className="space-y-2 pt-2">
                    <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">
                      Sequence preview
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {path.courses.map((course: string, idx: number) => (
                        <span
                          key={course}
                          className="text-[9px] font-bold bg-card/65 px-2 py-1 border border-border/40 rounded text-foreground/80"
                        >
                          {course.replace("linux-", "").replace("-basics", "").replace("-fundamentals", "").replace("-processes", "").replace("-project", " capstone").replace("-", " ")}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="pt-6">
                  <Link href={`/learning-paths/${path.id}`}>
                    <Button className="w-full bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl flex items-center justify-center space-x-2 py-2.5 shadow-sm transition-transform hover:scale-[1.01] cursor-pointer">
                      <span>Start Pathway</span>
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </DashboardShell>
  );
}
