import { apiClient } from "@/lib/api-client";

export interface LabSession {
  id: string;
  user_id: string;
  lab_name: string;
  container_id: string | null;
  status: "starting" | "running" | "stopped" | "expired";
  started_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface ValidationResponse {
  success: boolean;
  message: string;
}

export const labSessionService = {
  async launchLinuxLab(): Promise<LabSession> {
    const response = await apiClient.post("/labs/linux/launch");
    return response.data;
  },

  async stopLinuxLab(sessionId: string): Promise<LabSession> {
    const response = await apiClient.post(`/labs/linux/${sessionId}/stop`);
    return response.data;
  },

  async getActiveLinuxSession(): Promise<LabSession | null> {
    const response = await apiClient.get("/labs/linux/active");
    return response.data;
  },

  async validateLinuxTask(sessionId: string, taskId: number): Promise<ValidationResponse> {
    const response = await apiClient.post(`/labs/linux/${sessionId}/validate`, {
      task_id: taskId,
    });
    return response.data;
  },
};
