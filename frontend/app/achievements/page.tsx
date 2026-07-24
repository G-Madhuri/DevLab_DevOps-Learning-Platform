"use client";

import { useQuery } from "@tanstack/react-query";
import { labService } from "@/services/lab.service";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Trophy, Flame, Lock, ShieldAlert, BadgeCheck, CheckCircle2, Circle } from "lucide-react";

export default function AchievementsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["achievements_list"],
    queryFn: () => labService.listAchievements(),
  });

  const streak = data?.streak ?? 0;
  const badges = data?.badges ?? [];

  const pathBadges = badges.filter((b: any) => b.type === "learning_path");
  const streakBadges = badges.filter((b: any) => b.type === "streak");

  return (
    <DashboardShell>
      <div className="space-y-8">
        {/* Header Dashboard Grid */}
        <div className="flex flex-col md:flex-row gap-6 items-stretch">
          <div className="flex-1 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent rounded-2xl border border-primary/20 p-6 flex items-center space-x-4">
            <div className="p-3.5 bg-primary/20 rounded-xl text-primary animate-pulse">
              <Trophy className="h-7 w-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                My Achievements
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Unlock career specialization badges and maintain daily learning milestones.
              </p>
            </div>
          </div>

          <div className="bg-card rounded-2xl border border-border p-6 flex items-center space-x-4 min-w-[200px] shadow-sm">
            <div className="p-3 bg-orange-500/10 text-orange-500 rounded-xl">
              <Flame className="h-6 w-6 animate-bounce" />
            </div>
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Current Streak</p>
              <h2 className="text-3xl font-extrabold text-foreground mt-0.5">{streak} Days</h2>
            </div>
          </div>
        </div>

        {/* Career Specializations Path Badges */}
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-bold text-foreground">Career Roadmap Badges</h2>
            <p className="text-xs text-muted-foreground">Badges earned by completing specialized tracks on the career roadmap.</p>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 rounded-xl border border-border bg-card animate-pulse" />
              ))}
            </div>
          ) : pathBadges.length === 0 ? (
            <div className="rounded-xl border border-border bg-card p-6 text-center text-sm text-muted-foreground">
              No learning paths registered.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pathBadges.map((badge: any) => (
                <div
                  key={badge.id}
                  className={`group relative flex flex-col justify-between rounded-xl border p-5 transition-all duration-300 ${
                    badge.unlocked
                      ? "border-primary bg-primary/[0.02] shadow-sm"
                      : "border-border bg-card hover:border-border/80"
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                          badge.rarity === "Legendary" 
                            ? "bg-amber-500/10 text-amber-500 border border-amber-500/20"
                            : badge.rarity === "Epic"
                            ? "bg-purple-500/10 text-purple-500 border border-purple-500/20"
                            : "bg-muted text-muted-foreground border border-border"
                        }`}>
                          {badge.rarity}
                        </span>
                        {badge.unlocked && <BadgeCheck className="h-4 w-4 text-primary" />}
                      </div>
                      <h3 className="font-bold text-sm text-foreground line-clamp-1">{badge.title}</h3>
                      <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                        {badge.description}
                      </p>
                    </div>

                    <div className={`p-2.5 rounded-xl border ${
                      badge.unlocked 
                        ? "bg-primary/10 border-primary/20 text-primary" 
                        : "bg-muted border-border text-muted-foreground/60"
                    }`}>
                      {badge.unlocked ? <Trophy className="h-5 w-5" /> : <Lock className="h-5 w-5" />}
                    </div>
                  </div>

                  {/* Progress Indicator */}
                  <div className="mt-5 space-y-1.5">
                    <div className="flex justify-between text-[10px] text-muted-foreground font-semibold">
                      <span>Progress</span>
                      <span>{badge.completed_count} / {badge.total_count} Courses ({badge.progress}%)</span>
                    </div>
                    <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden border border-border/40">
                      <div 
                        className={`h-full transition-all duration-500 rounded-full ${
                          badge.unlocked ? "bg-primary" : "bg-muted-foreground/40"
                        }`}
                        style={{ width: `${badge.progress}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Daily Streak Milestones */}
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-bold text-foreground">Learning Streak Milestones</h2>
            <p className="text-xs text-muted-foreground">Unlock unique daily grind achievements by completing tasks consecutively.</p>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-28 rounded-xl border border-border bg-card animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {streakBadges.map((badge: any) => (
                <div
                  key={badge.id}
                  className={`group relative flex items-center space-x-4 rounded-xl border p-4 transition-all duration-300 ${
                    badge.unlocked
                      ? "border-orange-500 bg-orange-500/[0.01]"
                      : "border-border bg-card"
                  }`}
                >
                  <div className={`p-3 rounded-xl border transition-colors ${
                    badge.unlocked
                      ? "bg-orange-500/10 border-orange-500/20 text-orange-500"
                      : "bg-muted border-border text-muted-foreground/50"
                  }`}>
                    {badge.unlocked ? <Flame className="h-6 w-6" /> : <Lock className="h-6 w-6" />}
                  </div>

                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-bold text-sm text-foreground truncate">{badge.title}</h4>
                      <span className={`text-[8px] font-bold uppercase px-1.5 py-0.5 rounded ${
                        badge.unlocked ? "bg-orange-500/10 text-orange-500" : "bg-muted text-muted-foreground"
                      }`}>
                        {badge.target_days}D
                      </span>
                    </div>
                    <p className="text-[11px] text-muted-foreground line-clamp-1 leading-relaxed">
                      {badge.description}
                    </p>
                    <div className="flex items-center space-x-2 pt-1">
                      <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${badge.unlocked ? "bg-orange-500" : "bg-muted-foreground/35"}`}
                          style={{ width: `${badge.progress}%` }}
                        />
                      </div>
                      <span className="text-[9px] font-bold text-muted-foreground font-mono">{badge.completed_count}/{badge.total_count}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
