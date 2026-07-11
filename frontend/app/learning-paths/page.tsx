"use client";

import React from "react";
import Link from "next/link";
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
} from "lucide-react";

export default function LearningPathsPage() {
  const paths = [
    {
      id: "devops-beginner",
      title: "DevOps Beginner",
      description: "Learn command-line basics, source control, containers, automation pipelines, and infrastructure provisioning.",
      difficulty: "Beginner",
      duration: "24 hrs",
      courses: [
        "Linux",
        "Git",
        "Docker",
        "GitHub Actions",
        "Jenkins",
        "Terraform",
        "Monitoring"
      ],
      progress: 0,
      color: "from-emerald-500/20 via-emerald-500/5 to-transparent",
      accent: "text-emerald-500 border-emerald-500/20 bg-emerald-500/10",
    },
    {
      id: "cloud-engineer",
      title: "Cloud Engineer",
      description: "Master server configuration, network structures, Infrastructure as Code, and Amazon Web Services configurations.",
      difficulty: "Intermediate",
      duration: "18 hrs",
      courses: [
        "Linux",
        "Git",
        "Terraform",
        "AWS",
        "Monitoring"
      ],
      progress: 0,
      color: "from-amber-500/20 via-amber-500/5 to-transparent",
      accent: "text-amber-500 border-amber-500/20 bg-amber-500/10",
    },
    {
      id: "kubernetes-engineer",
      title: "Kubernetes Engineer",
      description: "Deploy and orchestrate massive scale containerized workloads, helm charts, GitOps, and observability pipelines.",
      difficulty: "Advanced",
      duration: "30 hrs",
      courses: [
        "Linux",
        "Docker",
        "Kubernetes",
        "Helm",
        "Argo CD",
        "Prometheus",
        "Grafana"
      ],
      progress: 0,
      color: "from-indigo-500/20 via-indigo-500/5 to-transparent",
      accent: "text-indigo-500 border-indigo-500/20 bg-indigo-500/10",
    },
  ];

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

      {/* Grid of Learning Paths */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {paths.map((path) => (
          <div
            key={path.id}
            className={`rounded-xl border border-border bg-gradient-to-b ${path.color} p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition-all duration-200 hover:border-primary/20 text-left`}
          >
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span
                  className={`px-2 py-0.5 border rounded-full text-[9px] font-bold uppercase tracking-wider ${path.accent}`}
                >
                  {path.difficulty}
                </span>
                <span className="text-[10px] text-muted-foreground font-semibold flex items-center">
                  <Clock className="h-3.5 w-3.5 mr-1" />
                  {path.duration}
                </span>
              </div>

              <div className="space-y-1">
                <h2 className="text-lg font-bold text-foreground tracking-tight">{path.title}</h2>
                <p className="text-xs text-muted-foreground leading-relaxed">{path.description}</p>
              </div>

              {/* Progress Tracker */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] font-bold text-foreground">
                  <span>PATH PROGRESS</span>
                  <span>{path.progress}%</span>
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden border border-border/50">
                  <div
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${path.progress}%` }}
                  />
                </div>
              </div>

              {/* Courses list step-by-step layout */}
              <div className="space-y-2 pt-2">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">
                  Courses Sequence
                </span>
                <div className="space-y-1.5">
                  {path.courses.map((course, idx) => (
                    <div
                      key={course}
                      className="flex items-center space-x-2 text-xs bg-card/60 p-2.5 rounded-lg border border-border/40 hover:bg-card hover:border-primary/10 transition-all"
                    >
                      <span className="text-[9px] font-extrabold text-muted-foreground bg-muted border border-border/50 h-5 w-5 flex items-center justify-center rounded-full shrink-0">
                        {idx + 1}
                      </span>
                      <span className="font-medium text-foreground/90 shrink-0">{course}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-6">
              <Link href="/labs">
                <Button className="w-full bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-bold rounded-xl flex items-center justify-center space-x-2 py-2.5 shadow-sm transition-transform hover:scale-[1.01] cursor-pointer">
                  <span>Start Learning Pathway</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        ))}
      </div>
    </DashboardShell>
  );
}
