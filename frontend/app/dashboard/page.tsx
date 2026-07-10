"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { labSessionService, LabSession } from "@/services/lab-session.service";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import {
  FlaskConical,
  Flame,
  Award,
  Zap,
  BookOpen,
  Calendar,
  Compass,
  ArrowRight,
  Terminal as TerminalIcon,
  Clock,
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const [quoteIndex, setQuoteIndex] = useState(0);

  const motivationalQuotes = [
    "Automation is the key to high-performance scale. Script once, deploy infinitely.",
    "Fail fast, learn faster. Every broken pipeline is a lesson in resilience.",
    "If it hurts, do it more often. Continuous integration makes deployment simple.",
    "Infrastructure as Code turns servers into software. Control configuration dynamically.",
    "Continuous learning is the bedrock of high-performing engineering organizations.",
  ];

  useEffect(() => {
    const day = new Date().getDate();
    setQuoteIndex(day % motivationalQuotes.length);
  }, []);

  // Fetch current active running session
  const { data: activeSession, isLoading: isLoadingSession } = useQuery<LabSession | null>({
    queryKey: ["active_linux_session"],
    queryFn: labSessionService.getActiveLinuxSession,
  });

  const stats = [
    {
      label: "Labs Completed",
      value: "0",
      icon: <FlaskConical className="h-5 w-5 text-indigo-500 dark:text-indigo-400" />,
      desc: "Finish labs to gain credentials",
    },
    {
      label: "Current Streak",
      value: "1 Day",
      icon: <Flame className="h-5 w-5 text-red-500 dark:text-red-400" />,
      desc: "Log in daily to keep streak",
    },
    {
      label: "XP Earned",
      value: "150",
      icon: <Zap className="h-5 w-5 text-amber-500 dark:text-amber-400" />,
      desc: "Experience Points level",
    },
    {
      label: "Active Labs",
      value: activeSession ? "1" : "0",
      icon: <Compass className="h-5 w-5 text-emerald-500 dark:text-emerald-400" />,
      desc: "Simultaneous active runtimes",
    },
  ];

  const upcomingFeatures = [
    {
      title: "Interactive Web Terminals",
      desc: "Connect directly to isolated sandboxes featuring full-featured Linux shells, Docker, and Kubernetes clusters in real-time.",
      badge: "Completed",
    },
    {
      title: "Automated Check Engine",
      desc: "Run direct validations that inspect your running configs, files, and endpoints to give immediate pass/fail feedback.",
      badge: "Completed",
    },
    {
      title: "Verify Certificates & Leaderboards",
      desc: "Earn shareable career credentials for your LinkedIn portfolio and compete on global experience boards.",
      badge: "Coming Soon",
    },
  ];

  return (
    <DashboardShell>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Welcome & Motivation Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Welcome Card */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h1 className="text-2xl font-bold text-foreground">
              Welcome back, {user?.name?.split(" ")[0]}! 👋
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Enter your live sandbox workspace or continue exploring the learning catalog modules.
            </p>
            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <Link href="/labs">
                <Button className="bg-primary hover:bg-primary/95 text-primary-foreground rounded-md flex items-center space-x-2">
                  <span>Explore Labs Catalog</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              {activeSession && (
                <Link href="/labs/linux-basics">
                  <Button variant="outline" className="border-emerald-500/30 hover:bg-emerald-500/5 text-emerald-600 rounded-md flex items-center space-x-2">
                    <TerminalIcon className="h-4 w-4" />
                    <span>Active Sandbox</span>
                  </Button>
                </Link>
              )}
            </div>
          </div>

          {/* Active Session Status Widget */}
          {activeSession && (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div className="space-y-1.5">
                <div className="flex items-center space-x-2">
                  <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">
                    Running Sandbox Session
                  </span>
                </div>
                <h3 className="text-base font-bold text-foreground">
                  Linux Command Line Basics
                </h3>
                <p className="text-xs text-muted-foreground flex items-center">
                  <Clock className="h-3.5 w-3.5 mr-1" />
                  Launched: {new Date(activeSession.started_at || "").toLocaleTimeString()}
                </p>
              </div>
              <Link href="/labs/linux-basics">
                <Button className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-bold px-5">
                  Continue Workspace
                </Button>
              </Link>
            </div>
          )}

          {/* Daily Motivation Card */}
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center space-x-2 text-xs text-primary font-bold uppercase tracking-wider mb-2">
              <Calendar className="h-4 w-4" />
              <span>Motivation for Today</span>
            </div>
            <p className="text-sm font-medium italic text-foreground leading-relaxed">
              &ldquo;{motivationalQuotes[quoteIndex]}&rdquo;
            </p>
          </div>
        </div>

        {/* Short Roadmaps Column */}
        <div className="space-y-6">
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm h-full flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-bold text-foreground mb-1">Roadmap</h2>
              <p className="text-xs text-muted-foreground mb-4">
                Here is what we implemented in Phase 3 &amp; future scopes:
              </p>
              <div className="space-y-3">
                {upcomingFeatures.map((feat, i) => (
                  <div key={i} className="p-3 bg-muted/40 rounded-lg border border-border/50 text-left">
                    <span className={`inline-block text-[9px] border px-1.5 py-0.5 rounded font-bold uppercase mb-1 ${
                      feat.badge === "Completed"
                        ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                        : "bg-primary/10 text-primary border-primary/20"
                    }`}>
                      {feat.badge}
                    </span>
                    <h4 className="text-xs font-bold text-foreground">{feat.title}</h4>
                    <p className="text-[11px] text-muted-foreground mt-0.5 leading-normal">
                      {feat.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold tracking-wider text-muted-foreground uppercase">
                {stat.label}
              </span>
              <div className="p-2 rounded-lg bg-muted">{stat.icon}</div>
            </div>
            <p className="text-3xl font-black text-foreground">{stat.value}</p>
            <p className="mt-1 text-[10px] text-muted-foreground leading-relaxed">
              {stat.desc}
            </p>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="p-6 border-b border-border bg-muted/20">
          <h2 className="text-lg font-bold text-foreground">Recent Activity</h2>
          <p className="text-xs text-muted-foreground mt-0.5">Your latest sandbox metrics</p>
        </div>
        {activeSession ? (
          <div className="divide-y divide-border">
            <div className="p-6 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-lg">
                  <TerminalIcon className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-foreground">
                    Linux Command Line Basics
                  </h4>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    Interactive shell active. Status: {activeSession.status}.
                  </p>
                </div>
              </div>
              <Link href="/labs/linux-basics">
                <Button size="sm" variant="ghost" className="text-xs font-bold flex items-center space-x-1">
                  <span>Open Console</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-muted border border-border/40">
              <FlaskConical className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-sm font-bold text-foreground mb-1">No sessions recorded</h3>
            <p className="text-xs text-muted-foreground max-w-sm leading-relaxed">
              Go to the Explorer catalog and spin up your first Ubuntu container sandbox!
            </p>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
