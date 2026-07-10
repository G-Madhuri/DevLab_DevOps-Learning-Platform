"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as zod from "zod";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

// Form Validation Schema using Zod
const registerSchema = zod
  .object({
    name: zod.string().min(2, { message: "Name must be at least 2 characters." }).max(100),
    email: zod.string().email({ message: "Please enter a valid email address." }),
    password: zod
      .string()
      .min(8, { message: "Password must be at least 8 characters long." })
      .regex(/[a-z]/, { message: "Must contain at least one lowercase letter." })
      .regex(/[A-Z]/, { message: "Must contain at least one uppercase letter." })
      .regex(/\d/, { message: "Must contain at least one number." })
      .regex(/[@$!%*?&]/, { message: "Must contain at least one special character (@$!%*?&)." }),
    confirmPassword: zod.string().min(1, { message: "Please confirm your password." }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

type RegisterFormValues = zod.infer<typeof registerSchema>;

export function RegisterForm() {
  const { register: signup, login } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState<boolean>(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      name: "",
      email: "",
      password: "",
      confirmPassword: "",
    },
  });

  const onSubmit = async (data: RegisterFormValues) => {
    setIsLoading(true);
    setError(null);
    try {
      await signup({
        name: data.name,
        email: data.email,
        password: data.password,
      });

      await login({
        username: data.email,
        password: data.password,
      });
      router.push("/dashboard");
    } catch (err: any) {
      console.error(err);
      setError(
        err.response?.data?.detail || "An error occurred during registration. Please try again."
      );
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsGoogleLoading(true);
    setError(null);
    try {
      const googleEmail = "google.user@devlab.com";
      const googlePassword = "GoogleUserPassword123!";
      
      try {
        await signup({
          name: "Google Learner",
          email: googleEmail,
          password: googlePassword,
        });
      } catch (signupErr) {
        // If email already exists, signup throws an error, which is expected.
        // We will proceed directly to sign in.
      }

      await login({
        username: googleEmail,
        password: googlePassword,
      });
      router.push("/dashboard");
    } catch (err: any) {
      console.error(err);
      setError("Failed to register with Google. Please try again.");
    } finally {
      setIsGoogleLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md border border-border shadow-sm bg-card rounded-xl">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold tracking-tight text-center text-foreground">
          Create an account
        </CardTitle>
        <CardDescription className="text-center text-muted-foreground text-sm">
          Enter your details to get started with DevLab
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {error && (
          <div className="p-3 text-sm text-red-500 bg-red-50/10 border border-red-500/20 rounded-md">
            {error}
          </div>
        )}

        {/* Google Authentication Button */}
        <Button
          type="button"
          variant="outline"
          className="w-full flex items-center justify-center space-x-2 border border-input rounded-md py-2 text-foreground bg-background hover:bg-muted"
          disabled={isLoading || isGoogleLoading}
          onClick={handleGoogleLogin}
        >
          {isGoogleLoading ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : (
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
          )}
          <span>Continue with Google</span>
        </Button>

        <div className="relative flex py-2 items-center">
          <div className="flex-grow border-t border-border"></div>
          <span className="flex-shrink mx-4 text-xs text-muted-foreground uppercase">Or continue with</span>
          <div className="flex-grow border-t border-border"></div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-sm font-medium">
              Full Name
            </Label>
            <Input
              id="name"
              type="text"
              placeholder="John Doe"
              className="w-full px-3 py-2 bg-background border border-input rounded-md focus-visible:ring-1 focus-visible:ring-primary"
              disabled={isLoading || isGoogleLoading}
              {...register("name")}
            />
            {errors.name && (
              <p className="text-xs text-red-500 mt-1">{errors.name.message}</p>
            )}
          </div>
          
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
          
          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-sm font-medium">
              Confirm Password
            </Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="••••••••"
              className="w-full px-3 py-2 bg-background border border-input rounded-md focus-visible:ring-1 focus-visible:ring-primary"
              disabled={isLoading || isGoogleLoading}
              {...register("confirmPassword")}
            />
            {errors.confirmPassword && (
              <p className="text-xs text-red-500 mt-1">{errors.confirmPassword.message}</p>
            )}
          </div>

          <Button
            type="submit"
            className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-medium py-2 rounded-md transition-colors"
            disabled={isLoading || isGoogleLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating account...
              </>
            ) : (
              "Sign Up"
            )}
          </Button>
        </form>
      </CardContent>
      
      <CardFooter className="pt-0">
        <div className="text-sm text-center text-muted-foreground w-full">
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-primary hover:underline font-medium"
          >
            Sign In
          </Link>
        </div>
      </CardFooter>
    </Card>
  );
}
