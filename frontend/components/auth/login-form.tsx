"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, X } from "lucide-react";

// Form Validation Schema using Zod
const loginSchema = zod.object({
  email: zod.string().email({ message: "Please enter a valid email address." }),
  password: zod.string().min(1, { message: "Password is required." }),
  rememberMe: zod.boolean().optional(),
});

type LoginFormValues = zod.infer<typeof loginSchema>;

export function LoginForm() {
  const { login, loginWithGoogle } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState<boolean>(false);
  const [isMockGoogleOpen, setIsMockGoogleOpen] = useState<boolean>(false);
  
  // Custom Google Account state
  const [customGoogleEmail, setCustomGoogleEmail] = useState("");
  const [customGoogleName, setCustomGoogleName] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
      rememberMe: false,
    },
  });

  const onSubmit = async (data: LoginFormValues) => {
    setIsLoading(true);
    setError(null);
    try {
      await login({
        username: data.email,
        password: data.password,
        remember_me: data.rememberMe,
      });
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail || "Invalid email or password. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customGoogleEmail || !customGoogleName) {
      setError("Please fill in both email and name for Google Sign-In.");
      return;
    }
    setIsGoogleLoading(true);
    setError(null);
    try {
      // Execute OAuth registration/login flow on the backend using user's specific details
      await loginWithGoogle(
        "mock-google-token-" + Math.random().toString(36).substring(7),
        customGoogleEmail,
        customGoogleName
      );
      setIsMockGoogleOpen(false);
    } catch (err: any) {
      console.error(err);
      setError("Failed to sign in with Google account. Please try again.");
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <>
      <Card className="w-full max-w-md border border-border shadow-sm bg-card rounded-xl">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold tracking-tight text-center text-foreground">
            Welcome back
          </CardTitle>
          <CardDescription className="text-center text-muted-foreground text-sm">
            Enter your email and password to access your dashboard
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-500 bg-red-50/10 border border-red-500/20 rounded-md">
              {error}
            </div>
          )}

          {/* Trigger Google Custom Account Modal */}
          <Button
            type="button"
            variant="outline"
            className="w-full flex items-center justify-center space-x-2 border border-input rounded-md py-2 text-foreground bg-background hover:bg-muted"
            disabled={isLoading || isGoogleLoading}
            onClick={() => setIsMockGoogleOpen(true)}
          >
            <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            <span>Continue with Google</span>
          </Button>

          <div className="relative flex py-2 items-center">
            <div className="flex-grow border-t border-border"></div>
            <span className="flex-shrink mx-4 text-xs text-muted-foreground uppercase">Or continue with</span>
            <div className="flex-grow border-t border-border"></div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium">
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                className="w-full px-3 py-2 bg-background border border-input rounded-md focus-visible:ring-1 focus-visible:ring-primary"
                disabled={isLoading || isGoogleLoading}
                {...register("email")}
              />
              {errors.email && (
                <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>
              )}
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">
                Password
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                className="w-full px-3 py-2 bg-background border border-input rounded-md focus-visible:ring-1 focus-visible:ring-primary"
                disabled={isLoading || isGoogleLoading}
                {...register("password")}
              />
              {errors.password && (
                <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="rememberMe"
                className="h-4 w-4 rounded border-border text-primary focus:ring-primary bg-background"
                {...register("rememberMe")}
              />
              <label
                htmlFor="rememberMe"
                className="text-xs text-muted-foreground cursor-pointer select-none"
              >
                Remember me
              </label>
            </div>

            <Button
              type="submit"
              className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-medium py-2 rounded-md transition-colors"
              disabled={isLoading || isGoogleLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </Button>
          </form>
        </CardContent>
        
        <CardFooter className="pt-0">
          <div className="text-sm text-center text-muted-foreground w-full">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="text-primary hover:underline font-medium"
            >
              Register
            </Link>
          </div>
        </CardFooter>
      </Card>

      {/* Google Chooser Account Modal */}
      {isMockGoogleOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="relative w-full max-w-sm rounded-xl border border-border bg-card p-6 shadow-xl space-y-6">
            <button
              onClick={() => setIsMockGoogleOpen(false)}
              className="absolute right-4 top-4 rounded-md p-1 hover:bg-muted text-muted-foreground"
            >
              <X className="h-4 w-4" />
            </button>

            {/* Header */}
            <div className="flex flex-col items-center text-center space-y-2">
              <svg className="h-8 w-8" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <h3 className="text-lg font-bold text-foreground">Sign in with Google</h3>
              <p className="text-xs text-muted-foreground">
                Enter your Google account credentials to sync DevLab locally
              </p>
            </div>

            {/* Inputs */}
            <form onSubmit={handleGoogleLogin} className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="google_name" className="text-xs font-semibold">
                  Google Account Name
                </Label>
                <Input
                  id="google_name"
                  placeholder="e.g. John Doe"
                  className="bg-background border border-input text-sm"
                  required
                  value={customGoogleName}
                  onChange={(e) => setCustomGoogleName(e.target.value)}
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="google_email" className="text-xs font-semibold">
                  Google Email Address
                </Label>
                <Input
                  id="google_email"
                  type="email"
                  placeholder="e.g. john.doe@gmail.com"
                  className="bg-background border border-input text-sm"
                  required
                  value={customGoogleEmail}
                  onChange={(e) => setCustomGoogleEmail(e.target.value)}
                />
              </div>

              <Button
                type="submit"
                disabled={isGoogleLoading}
                className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-semibold text-xs py-2 rounded-md transition-colors"
              >
                {isGoogleLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Continue to DevLab"
                )}
              </Button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
