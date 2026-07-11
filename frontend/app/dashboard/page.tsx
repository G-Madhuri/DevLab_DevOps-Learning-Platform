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
  Zap,
  BookOpen,
  Calendar,
  Compass,
  ArrowRight,
  Terminal as TerminalIcon,
  Clock,
  Layers,
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
  const { data: activeSession } = useQuery<LabSession | null>({
    queryKey: ["active_linux_session"],
    queryFn: () => labSessionService.getActiveLinuxSession(),
  });

  // Fetch recent session logs
  const { data: sessionsData } = useQuery({
    queryKey: ["user_lab_sessions"],
    queryFn: () => labSessionService.getSessions(0, 5),
  });
  const recentSessions = sessionsData?.sessions || [];

  // Query progress records for Linux Basics
  const { data: linuxProgress } = useQuery({
    queryKey: ["course_progress", "linux-basics"],
    queryFn: () => labSessionService.getCourseProgress("linux-basics"),
  });

  // Query progress records for Docker Basics
  const { data: dockerProgress } = useQuery({
    queryKey: ["course_progress", "docker-basics"],
    queryFn: () => labSessionService.getCourseProgress("docker-basics"),
  });

  const totalCompleted =
    (linuxProgress?.completed_lessons?.length || 0) +
    (dockerProgress?.completed_lessons?.length || 0);

  const stats = [
    {
      label: "Steps Verified",
      value: totalCompleted.toString(),
      icon: <FlaskConical className="h-5 w-5 text-indigo-500 dark:text-indigo-400" />,
      desc: "Completed lesson exercises",
    },
    {
      label: "Current Streak",
      value: user?.streak ? `${user.streak} ${user.streak === 1 ? "Day" : "Days"}` : "1 Day",
      icon: <Flame className="h-5 w-5 text-red-500 dark:text-red-400" />,
      desc: "Log in daily to keep streak",
    },
    {
      label: "XP Earned",
      value: (totalCompleted * 50 + 150).toString(),
      icon: <Zap className="h-5 w-5 text-amber-500 dark:text-amber-400" />,
      desc: "Experience points level",
    },
    {
      label: "Active Labs",
      value: activeSession ? "1" : "0",
      icon: <Compass className="h-5 w-5 text-emerald-500 dark:text-emerald-400" />,
      desc: "Simultaneous running sandboxes",
    },
  ];

  return (
    <DashboardShell>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Welcome & Active session */}
        <div className="lg:col-span-2 space-y-6">
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
                <Link href={activeSession.lab_name === "docker-basics" ? "/labs/docker-basics" : "/labs/linux-basics"}>
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
                <h3 className="text-base font-bold text-foreground capitalize">
                  {activeSession.lab_name.replace("-basics", " Basics").replace("-", " ")}
                </h3>
                <p className="text-xs text-muted-foreground flex items-center">
                  <Clock className="h-3.5 w-3.5 mr-1" />
                  Launched: {new Date(activeSession.started_at || "").toLocaleTimeString()}
                </p>
              </div>
              <Link href={activeSession.lab_name === "docker-basics" ? "/labs/docker-basics" : "/labs/linux-basics"}>
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

        {/* Course Progress Section */}
        <div className="space-y-6">
          <div className="rounded-xl border border-border bg-card p-6 shadow-sm h-full flex flex-col justify-between">
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-bold text-foreground">Course Progress</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Track your active DevOps learning pathways.
                </p>
              </div>

              {/* Linux Progress Card */}
              <div className="p-4 bg-muted/40 rounded-xl border border-border/50 space-y-2.5 text-left">
                <div className="flex justify-between items-center text-xs font-bold">
                  <span className="text-foreground">Linux Basics</span>
                  <span className="text-primary font-black">{linuxProgress?.percentage || 0}%</span>
                </div>
                <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                    style={{ width: `${linuxProgress?.percentage || 0}%` }}
                  />
                </div>
                <div className="flex justify-between items-center pt-1">
                  <span className="text-[10px] text-muted-foreground font-semibold">
                    {linuxProgress?.completed_lessons?.length || 0} / 20 steps
                  </span>
                  <Link href="/labs/linux-basics">
                    <Button size="sm" className="h-6 text-[10px] px-2.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/10 font-bold rounded">
                      Continue
                    </Button>
                  </Link>
                </div>
              </div>

              {/* Docker Progress Card */}
              <div className="p-4 bg-muted/40 rounded-xl border border-border/50 space-y-2.5 text-left">
                <div className="flex justify-between items-center text-xs font-bold">
                  <span className="text-foreground">Docker Basics</span>
                  <span className="text-primary font-black">{dockerProgress?.percentage || 0}%</span>
                </div>
                <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all duration-300"
                    style={{ width: `${dockerProgress?.percentage || 0}%` }}
                  />
                </div>
                <div className="flex justify-between items-center pt-1">
                  <span className="text-[10px] text-muted-foreground font-semibold">
                    {dockerProgress?.completed_lessons?.length || 0} / 18 steps
                  </span>
                  <Link href="/labs/docker-basics">
                    <Button size="sm" className="h-6 text-[10px] px-2.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/10 font-bold rounded">
                      Continue
                    </Button>
                  </Link>
                </div>
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
        {recentSessions.length > 0 ? (
          <div className="divide-y divide-border">
            {recentSessions.map((sess: LabSession) => {
              const isRunning = sess.status === "running" || sess.status === "starting";
              return (
                <div key={sess.id} className="p-6 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div
                      className={`p-2 rounded-lg border ${
                        isRunning
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-600 animate-pulse"
                          : "bg-muted border-border/40 text-muted-foreground"
                      }`}
                    >
                      <TerminalIcon className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-foreground capitalize">
                        {sess.lab_name.replace("-basics", " Basics").replace("-", " ")}
                      </h4>
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        {isRunning
                          ? `Interactive sandbox container active. Status: ${sess.status}.`
                          : `Sandbox session finished. Status: ${sess.status}.`}
                      </p>
                      <p className="text-[9px] text-muted-foreground/70 font-mono mt-0.5">
                        ID: {sess.id.substring(0, 8)}... | Started: {new Date(sess.started_at || sess.created_at || "").toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <Link href={sess.lab_name === "docker-basics" ? "/labs/docker-basics" : "/labs/linux-basics"}>
                    <Button size="sm" variant="ghost" className="text-xs font-bold flex items-center space-x-1">
                      <span>{isRunning ? "Open Console" : "Restart Lab"}</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>
              );
            })}
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
