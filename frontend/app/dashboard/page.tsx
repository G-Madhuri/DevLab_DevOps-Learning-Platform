"use client";

import { DashboardShell } from "@/components/layout/dashboard-shell";
import { useAuth } from "@/hooks/use-auth";
import { BookOpen, FlaskConical, Star, Activity } from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();

  const stats = [
    { label: "Labs Completed", value: "0", icon: <FlaskConical className="h-5 w-5 text-primary" />, description: "Total labs finished" },
    { label: "XP Earned", value: "0", icon: <Star className="h-5 w-5 text-amber-500" />, description: "Experience points" },
    { label: "Active Labs", value: "0", icon: <Activity className="h-5 w-5 text-emerald-500" />, description: "Currently running" },
    { label: "Courses", value: "0", icon: <BookOpen className="h-5 w-5 text-indigo-500" />, description: "Enrolled courses" },
  ];

  return (
    <DashboardShell>
      {/* Welcome card */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-foreground">
          Welcome back, {user?.name?.split(" ")[0]} 👋
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your DevOps learning journey starts here. Explore labs and level up your skills.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <div key={i} className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-muted-foreground">{stat.label}</span>
              <div className="p-2 rounded-lg bg-muted">{stat.icon}</div>
            </div>
            <p className="text-3xl font-bold text-foreground">{stat.value}</p>
            <p className="mt-1 text-xs text-muted-foreground">{stat.description}</p>
          </div>
        ))}
      </div>

      {/* Recent Activity - Empty State */}
      <div className="rounded-xl border border-border bg-card shadow-sm">
        <div className="p-6 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">Recent Activity</h2>
          <p className="text-sm text-muted-foreground mt-1">Your latest lab sessions and completions</p>
        </div>
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <FlaskConical className="h-8 w-8 text-muted-foreground" />
          </div>
          <h3 className="text-base font-semibold text-foreground mb-1">No activity yet</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Launch your first lab to start tracking your progress. Lab environments coming in Phase 2.
          </p>
        </div>
      </div>
    </DashboardShell>
  );
}
