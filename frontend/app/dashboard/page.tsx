"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { labSessionService, LabSession } from "@/services/lab-session.service";
import { labService } from "@/services/lab.service";
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

  // Fetch all active running sessions
  const { data: activeSessions = [] } = useQuery<LabSession[]>({
    queryKey: ["all_active_sessions"],
    queryFn: () => labSessionService.getAllActiveLinuxSessions(),
  });

  // Fetch recent session logs
  const { data: sessionsData } = useQuery({
    queryKey: ["user_lab_sessions"],
    queryFn: () => labSessionService.getSessions(0, 5),
  });
  const recentSessions = sessionsData?.sessions || [];

  // Query Academies list (keeps progress synchronizations instant)
  const { data: academies = [] } = useQuery({
    queryKey: ["academies_list"],
    queryFn: () => labService.listAcademies(),
  });

  const linuxAcademy = academies.find((a) => a.id === "linux");
  const dockerAcademy = academies.find((a) => a.id === "docker");

  // Sum up all verified lessons across all academies
  let totalCompleted = 0;
  academies.forEach((academy) => {
    academy.courses?.forEach((c: any) => {
      totalCompleted += c.completed_lessons?.length || 0;
    });
  });

  const linuxTotalSteps = linuxAcademy?.courses?.reduce((acc: number, c: any) => acc + (c.completed_lessons?.length || 0), 0) || 0;
  const linuxMaxSteps = 75; // 5 courses * 15 lessons

  const dockerTotalSteps = dockerAcademy?.courses?.reduce((acc: number, c: any) => acc + (c.completed_lessons?.length || 0), 0) || 0;
  const dockerMaxSteps = 18; // 1 course * 18 lessons

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
      desc: "Dynamic points breakdown",
    },
    {
      label: "Certificates",
      value: (linuxAcademy?.certificate_unlocked ? 1 : 0).toString(),
      icon: <Layers className="h-5 w-5 text-emerald-500 dark:text-emerald-400" />,
      desc: "Unlocked achievements",
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
                <Button className="bg-primary hover:bg-primary/95 text-primary-foreground rounded-md flex items-center space-x-2 animate-pulse">
                  <span>Explore Academies Catalog</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              {activeSessions.length > 0 && (
                <Link href={activeSessions[0].lab_name === "docker-basics" ? "/labs/docker-basics" : "/labs/linux-basics"}>
                  <Button variant="outline" className="border-emerald-500/30 hover:bg-emerald-500/5 text-emerald-600 rounded-md flex items-center space-x-2">
                    <TerminalIcon className="h-4 w-4" />
                    <span>Active Sandbox ({activeSessions.length})</span>
                  </Button>
                </Link>
              )}
            </div>
          </div>

          {/* Active Session Status Widgets */}
          {activeSessions.map((sess: LabSession) => (
            <div key={sess.id} className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 animate-fade-in">
              <div className="space-y-1.5">
                <div className="flex items-center space-x-2">
                  <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">
                    Running Sandbox Session
                  </span>
                </div>
                <h3 className="text-base font-bold text-foreground capitalize">
                  {sess.lab_name.replace("-basics", " Basics").replace("-", " ")}
                </h3>
                <p className="text-xs text-muted-foreground flex items-center">
                  <Clock className="h-3.5 w-3.5 mr-1" />
                  Launched: {new Date(sess.started_at || "").toLocaleTimeString()}
                </p>
              </div>
              <Link href={sess.lab_name === "docker-basics" ? "/labs/docker-basics" : "/labs/linux-basics"}>
                <Button className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-xs font-bold px-5">
                  Continue Workspace
                </Button>
              </Link>
            </div>
          ))}

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
                <h2 className="text-lg font-bold text-foreground">Academy Progress</h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Track your active DevOps learning pathways.
                </p>
              </div>

              {/* Linux Progress Card */}
              <div className="p-4 bg-muted/40 rounded-xl border border-border/50 space-y-2.5 text-left transition-all hover:bg-muted/60">
                <div className="flex justify-between items-center text-xs font-bold">
                  <span className="text-foreground">Linux Academy</span>
                  <span className="text-primary font-black">{linuxAcademy?.progress || 0}%</span>
                </div>
                <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                    style={{ width: `${linuxAcademy?.progress || 0}%` }}
                  />
                </div>
                <div className="flex justify-between items-center pt-1">
                  <span className="text-[10px] text-muted-foreground font-semibold">
                    {linuxTotalSteps} / {linuxMaxSteps} steps
                  </span>
                  <Link href="/labs">
                    <Button size="sm" className="h-6 text-[10px] px-2.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/10 font-bold rounded">
                      Continue
                    </Button>
                  </Link>
                </div>
              </div>

              {/* Docker Progress Card */}
              <div className="p-4 bg-muted/40 rounded-xl border border-border/50 space-y-2.5 text-left transition-all hover:bg-muted/60">
                <div className="flex justify-between items-center text-xs font-bold">
                  <span className="text-foreground">Docker Academy</span>
                  <span className="text-primary font-black">{dockerAcademy?.progress || 0}%</span>
                </div>
                <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full transition-all duration-300"
                    style={{ width: `${dockerAcademy?.progress || 0}%` }}
                  />
                </div>
                <div className="flex justify-between items-center pt-1">
                  <span className="text-[10px] text-muted-foreground font-semibold">
                    {dockerTotalSteps} / {dockerMaxSteps} steps
                  </span>
                  <Link href="/labs">
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
              {stat.icon}
            </div>
            <div className="flex flex-col">
              <span className="text-2xl font-black text-foreground tracking-tight">
                {stat.value}
              </span>
              <span className="text-[10px] text-muted-foreground mt-1">
                {stat.desc}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Recent activity log */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-muted-foreground mb-4">
          <BookOpen className="h-4 w-4 text-primary" />
          <span>Recent Activity Feed</span>
        </div>

        {recentSessions.length === 0 ? (
          <div className="text-center py-6 text-xs text-muted-foreground">
            No recent sandbox activities found. Go launch a course lab to get started!
          </div>
        ) : (
          <div className="space-y-4">
            {recentSessions.map((sess: LabSession) => (
              <div
                key={sess.id}
                className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-border/40 last:border-0 last:pb-0 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-foreground capitalize">
                      {sess.lab_name.replace("-basics", " Basics").replace("-", " ")}
                    </span>
                    <span
                      className={`px-2 py-0.5 border rounded-full text-[9px] font-bold uppercase ${
                        sess.status === "running"
                          ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
                          : sess.status === "stopped"
                          ? "bg-slate-500/10 text-slate-600 border-slate-500/20"
                          : "bg-red-500/10 text-red-600 border-red-500/20"
                      }`}
                    >
                      {sess.status}
                    </span>
                  </div>
                  <p className="text-[10px] text-muted-foreground">
                    ID: {sess.id.slice(0, 8)}... | Created at: {new Date(sess.started_at || "").toLocaleString()}
                  </p>
                </div>
                <div className="flex space-x-2 w-full sm:w-auto justify-end">
                  <Link href={sess.lab_name === "docker-basics" ? "/labs/docker-basics" : "/labs/linux-basics"}>
                    <Button size="sm" variant="outline" className="h-7 text-[10px] rounded">
                      Open Console
                    </Button>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
