"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { RegisterForm } from "@/components/auth/register-form";
import Link from "next/link";
import { Terminal } from "lucide-react";

export default function RegisterPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // Redirect authenticated users to the dashboard
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading || isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground flex items-center space-x-2">
          <Terminal className="h-6 w-6 animate-spin" />
          <span>Loading session...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 bg-slate-50 dark:bg-slate-950/40">
      <div className="mb-6 flex items-center space-x-2">
        <Link href="/" className="flex items-center space-x-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <Terminal className="h-5 w-5" />
          </div>
          <span className="text-xl font-bold tracking-tight text-foreground">
            DevLab
          </span>
        </Link>
      </div>
      <RegisterForm />
    </div>
  );
}
