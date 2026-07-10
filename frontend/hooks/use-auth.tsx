"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { authService } from "@/services/auth.service";
import { getAccessToken, clearTokens } from "@/lib/api-client";
import { User } from "@/types";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: any) => Promise<any>;
  register: (data: any) => Promise<any>;
  logout: () => void;
  updateProfile: (data: any) => Promise<any>;
  isLoggingOut: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [hasToken, setHasToken] = useState<boolean>(false);

  // Sync token presence on mount and token changes
  useEffect(() => {
    setHasToken(!!getAccessToken());
  }, []);

  // Fetch the current user profile if a token exists
  const {
    data: user,
    isLoading: isFetchingUser,
    error,
  } = useQuery({
    queryKey: ["current_user"],
    queryFn: authService.getMe,
    enabled: hasToken,
    retry: false,
  });

  // Handle token issues (like invalid or expired token on initial load)
  useEffect(() => {
    if (error) {
      clearTokens();
      setHasToken(false);
      queryClient.setQueryData(["current_user"], null);
    }
  }, [error, queryClient]);

  // Login Mutation
  const loginMutation = useMutation({
    mutationFn: authService.login,
    onSuccess: (data) => {
      setHasToken(true);
      queryClient.setQueryData(["current_user"], data.user);
      queryClient.invalidateQueries({ queryKey: ["current_user"] });
      router.push("/dashboard");
    },
  });

  // Register Mutation
  const registerMutation = useMutation({
    mutationFn: authService.register,
  });

  // Logout Mutation
  const logoutMutation = useMutation({
    mutationFn: authService.logout,
    onSuccess: () => {
      setHasToken(false);
      queryClient.setQueryData(["current_user"], null);
      queryClient.clear();
      router.push("/login");
    },
  });

  // Update Profile Mutation
  const updateProfileMutation = useMutation({
    mutationFn: authService.updateMe,
    onSuccess: (updatedUser) => {
      queryClient.setQueryData(["current_user"], updatedUser);
    },
  });

  const value = {
    user: user || null,
    isLoading: isFetchingUser && hasToken,
    isAuthenticated: !!user,
    login: async (data: any) => loginMutation.mutateAsync(data),
    register: async (data: any) => registerMutation.mutateAsync(data),
    logout: () => logoutMutation.mutate(),
    updateProfile: async (data: any) => updateProfileMutation.mutateAsync(data),
    isLoggingOut: logoutMutation.isPending,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
