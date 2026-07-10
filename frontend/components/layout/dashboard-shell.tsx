"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import { Button } from "@/components/ui/button";
import {
  Terminal,
  LayoutDashboard,
  FlaskConical,
  BookOpen,
  Trophy,
  Award,
  User,
  Settings,
  LogOut,
  Menu,
  X,
  Loader2,
} from "lucide-react";

interface DashboardShellProps {
  children: React.ReactNode;
}

export function DashboardShell({ children }: DashboardShellProps) {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="text-sm text-muted-foreground">Verifying session...</span>
        </div>
      </div>
    );
  }

  // Configured with exact required list
  const navItems = [
    {
      label: "Dashboard",
      href: "/dashboard",
      icon: <LayoutDashboard className="h-4 w-4" />,
      active: pathname === "/dashboard",
      disabled: false,
    },
    {
      label: "Labs",
      href: "/labs",
      icon: <FlaskConical className="h-4 w-4" />,
      active: pathname.startsWith("/labs"),
      disabled: false,
    },
    {
      label: "Learning Paths",
      href: "#",
      icon: <BookOpen className="h-4 w-4" />,
      active: false,
      disabled: true,
    },
    {
      label: "Achievements",
      href: "#",
      icon: <Trophy className="h-4 w-4" />,
      active: false,
      disabled: true,
    },
    {
      label: "Certificates",
      href: "#",
      icon: <Award className="h-4 w-4" />,
      active: false,
      disabled: true,
    },
    {
      label: "Profile",
      href: "/profile",
      icon: <User className="h-4 w-4" />,
      active: pathname === "/profile",
      disabled: false,
    },
    {
      label: "Settings",
      href: "/settings",
      icon: <Settings className="h-4 w-4" />,
      active: pathname === "/settings",
      disabled: false,
    },
  ];

  const SidebarNav = () => (
    <div className="flex h-full flex-col justify-between p-4 bg-card border-r border-border">
      <div className="space-y-6">
        {/* Brand */}
        <Link href="/" className="flex items-center space-x-2 px-2 py-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <Terminal className="h-4 w-4" />
          </div>
          <span className="text-md font-bold tracking-tight text-foreground">DevLab</span>
        </Link>

        {/* Nav links */}
        <nav className="space-y-1">
          {navItems.map((item, i) =>
            item.disabled ? (
              <div
                key={i}
                className="flex items-center space-x-3 px-3 py-2 text-sm font-medium text-muted-foreground/50 cursor-not-allowed rounded-md hover:bg-transparent"
                title="Coming soon in future phases"
              >
                {item.icon}
                <span>{item.label}</span>
                <span className="ml-auto text-[9px] bg-muted text-muted-foreground border border-border/40 px-1 rounded font-normal uppercase">
                  Soon
                </span>
              </div>
            ) : (
              <Link
                key={i}
                href={item.href}
                onClick={() => setIsMobileOpen(false)}
                className={`flex items-center space-x-3 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  item.active
                    ? "bg-primary text-primary-foreground font-semibold"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            )
          )}
        </nav>
      </div>

      {/* User + Logout */}
      <div className="space-y-3 pt-4 border-t border-border">
        <div className="flex items-center space-x-3 px-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-xs uppercase shrink-0">
            {user?.name?.substring(0, 2)}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-semibold truncate text-foreground">{user?.name}</p>
            <p className="text-[10px] text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center space-x-3 px-3 py-2 text-sm font-medium rounded-md text-red-500 hover:bg-red-500/10 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );

  const pageTitle =
    pathname === "/dashboard"
      ? "Workspace"
      : pathname.startsWith("/labs")
      ? "Lab Explorer"
      : pathname === "/profile"
      ? "My Profile"
      : "Settings";

  return (
    <div className="flex min-h-screen bg-background text-foreground transition-colors duration-200">
      {/* Desktop Sidebar */}
      <aside className="hidden md:block w-64 shrink-0 h-screen sticky top-0">
        <SidebarNav />
      </aside>

      {/* Mobile Sidebar Overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div className="w-64 shrink-0 h-full shadow-xl">
            <SidebarNav />
          </div>
          <div
            className="flex-1 bg-black/40"
            onClick={() => setIsMobileOpen(false)}
          />
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex h-16 items-center justify-between px-4 sm:px-6 border-b border-border bg-card/50 backdrop-blur-md sticky top-0 z-40">
          <div className="flex items-center">
            <button
              className="md:hidden mr-3 p-1.5 rounded-md hover:bg-muted text-foreground"
              onClick={() => setIsMobileOpen(!isMobileOpen)}
            >
              {isMobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            <h2 className="text-sm font-bold tracking-tight text-foreground">{pageTitle}</h2>
          </div>
          <ThemeToggle />
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          <div className="mx-auto max-w-5xl space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
