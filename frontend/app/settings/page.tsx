"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";
import { User, LogOut, Palette } from "lucide-react";

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <DashboardShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-bold">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your account preferences</p>
        </div>

        {/* Theme */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-4">
            <Palette className="h-5 w-5 text-primary" />
            <div>
              <h2 className="text-base font-semibold">Appearance</h2>
              <p className="text-xs text-muted-foreground">Toggle between light and dark mode</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <ThemeToggle />
            <span className="text-sm text-muted-foreground">Switch theme</span>
          </div>
        </div>

        {/* Profile */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-4">
            <User className="h-5 w-5 text-primary" />
            <div>
              <h2 className="text-base font-semibold">Account</h2>
              <p className="text-xs text-muted-foreground">Manage your profile information</p>
            </div>
          </div>
          <div className="flex items-center space-x-4 mb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm uppercase">
              {user?.name?.substring(0, 2)}
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">{user?.name}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
          </div>
          <Link href="/profile">
            <Button variant="outline" className="text-sm">Edit Profile</Button>
          </Link>
        </div>

        {/* Logout */}
        <div className="rounded-xl border border-destructive/20 bg-card p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-4">
            <LogOut className="h-5 w-5 text-red-500" />
            <div>
              <h2 className="text-base font-semibold">Sign Out</h2>
              <p className="text-xs text-muted-foreground">Sign out of your DevLab account</p>
            </div>
          </div>
          <Button
            onClick={logout}
            variant="outline"
            className="text-red-500 border-red-500/30 hover:bg-red-50/10 hover:text-red-600 text-sm"
          >
            Logout
          </Button>
        </div>
      </div>
    </DashboardShell>
  );
}
