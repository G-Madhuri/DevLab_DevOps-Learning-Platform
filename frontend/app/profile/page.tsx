"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAuth } from "@/hooks/use-auth";
import { DashboardShell } from "@/components/layout/dashboard-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, User, Calendar, Mail } from "lucide-react";

const profileSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters").max(100),
});

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required"),
    new_password: z
      .string()
      .min(8)
      .regex(/[a-z]/, "Must contain lowercase")
      .regex(/[A-Z]/, "Must contain uppercase")
      .regex(/\d/, "Must contain a number")
      .regex(/[@$!%*?&]/, "Must contain a special character"),
    confirm_password: z.string(),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type ProfileValues = z.infer<typeof profileSchema>;
type PasswordValues = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const { user, updateProfile } = useAuth();
  const [nameSuccess, setNameSuccess] = useState(false);
  const [pwdSuccess, setPwdSuccess] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [pwdError, setPwdError] = useState<string | null>(null);

  const nameForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { name: user?.name || "" },
  });

  const pwdForm = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: "", new_password: "", confirm_password: "" },
  });

  const onUpdateName = async (data: ProfileValues) => {
    setNameError(null);
    setNameSuccess(false);
    try {
      await updateProfile({ name: data.name });
      setNameSuccess(true);
      setTimeout(() => setNameSuccess(false), 3000);
    } catch (err: any) {
      setNameError(err?.response?.data?.detail || "Failed to update name.");
    }
  };

  const onUpdatePassword = async (data: PasswordValues) => {
    setPwdError(null);
    setPwdSuccess(false);
    try {
      await updateProfile({ current_password: data.current_password, new_password: data.new_password });
      setPwdSuccess(true);
      pwdForm.reset();
      setTimeout(() => setPwdSuccess(false), 3000);
    } catch (err: any) {
      setPwdError(err?.response?.data?.detail || "Failed to update password.");
    }
  };

  const joinedDate = user?.created_at
    ? new Date(user.created_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })
    : "—";

  return (
    <DashboardShell>
      {/* Profile Info Card */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h1 className="text-xl font-bold mb-4">My Profile</h1>
        <div className="flex items-center space-x-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-xl uppercase">
            {user?.name?.substring(0, 2)}
          </div>
          <div className="space-y-1">
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <User className="h-4 w-4" />
              <span className="font-medium text-foreground">{user?.name}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <Mail className="h-4 w-4" />
              <span>{user?.email}</span>
            </div>
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span>Joined {joinedDate}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Update Name */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-1">Update Name</h2>
        <p className="text-sm text-muted-foreground mb-4">Change your display name</p>
        <form onSubmit={nameForm.handleSubmit(onUpdateName)} className="space-y-4 max-w-sm">
          {nameError && <p className="text-sm text-red-500 bg-red-50/10 border border-red-500/20 rounded p-2">{nameError}</p>}
          {nameSuccess && <p className="text-sm text-emerald-500 bg-emerald-50/10 border border-emerald-500/20 rounded p-2">Name updated successfully!</p>}
          <div className="space-y-1">
            <Label htmlFor="name">Full Name</Label>
            <Input id="name" {...nameForm.register("name")} />
            {nameForm.formState.errors.name && (
              <p className="text-xs text-red-500">{nameForm.formState.errors.name.message}</p>
            )}
          </div>
          <Button type="submit" disabled={nameForm.formState.isSubmitting} className="bg-primary hover:bg-primary/90 text-primary-foreground">
            {nameForm.formState.isSubmitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</> : "Save Name"}
          </Button>
        </form>
      </div>

      {/* Update Password */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-1">Change Password</h2>
        <p className="text-sm text-muted-foreground mb-4">Update your login password</p>
        <form onSubmit={pwdForm.handleSubmit(onUpdatePassword)} className="space-y-4 max-w-sm">
          {pwdError && <p className="text-sm text-red-500 bg-red-50/10 border border-red-500/20 rounded p-2">{pwdError}</p>}
          {pwdSuccess && <p className="text-sm text-emerald-500 bg-emerald-50/10 border border-emerald-500/20 rounded p-2">Password changed successfully!</p>}
          <div className="space-y-1">
            <Label htmlFor="current_password">Current Password</Label>
            <Input id="current_password" type="password" {...pwdForm.register("current_password")} />
            {pwdForm.formState.errors.current_password && (
              <p className="text-xs text-red-500">{pwdForm.formState.errors.current_password.message}</p>
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="new_password">New Password</Label>
            <Input id="new_password" type="password" {...pwdForm.register("new_password")} />
            {pwdForm.formState.errors.new_password && (
              <p className="text-xs text-red-500">{pwdForm.formState.errors.new_password.message}</p>
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="confirm_password">Confirm New Password</Label>
            <Input id="confirm_password" type="password" {...pwdForm.register("confirm_password")} />
            {pwdForm.formState.errors.confirm_password && (
              <p className="text-xs text-red-500">{pwdForm.formState.errors.confirm_password.message}</p>
            )}
          </div>
          <Button type="submit" disabled={pwdForm.formState.isSubmitting} className="bg-primary hover:bg-primary/90 text-primary-foreground">
            {pwdForm.formState.isSubmitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Updating...</> : "Change Password"}
          </Button>
        </form>
      </div>
    </DashboardShell>
  );
}
