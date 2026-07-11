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

export interface CourseProgressInfo {
  course_slug: string;
  completed_lessons: number[];
  current_lesson_id: number;
  percentage: number;
}

export const labSessionService = {
  async launchLinuxLab(labName: string = "linux-basics"): Promise<LabSession> {
    const response = await apiClient.post(`/labs/linux/launch?lab_name=${labName}`);
    return response.data;
  },

  async stopLinuxLab(sessionId: string): Promise<LabSession> {
    const response = await apiClient.post(`/labs/linux/${sessionId}/stop`);
    return response.data;
  },

  async getActiveLinuxSession(labName?: string): Promise<LabSession | null> {
    const url = labName ? `/labs/linux/active?lab_name=${labName}` : "/labs/linux/active";
    const response = await apiClient.get(url);
    return response.data;
  },

  async getAllActiveLinuxSessions(): Promise<LabSession[]> {
    const response = await apiClient.get("/labs/linux/active/all");
    return response.data;
  },

  async validateLinuxTask(sessionId: string, taskId: number, courseSlug?: string): Promise<ValidationResponse> {
    const response = await apiClient.post(`/labs/linux/${sessionId}/validate`, {
      task_id: taskId,
      course_slug: courseSlug,
    });
    return response.data;
  },

  async getCourseLessons(courseSlug: string): Promise<any[]> {
    const response = await apiClient.get(`/labs/linux/${courseSlug}/lessons`);
    return response.data;
  },

  async getCourseDetails(courseSlug: string): Promise<any> {
    const response = await apiClient.get(`/labs/linux/${courseSlug}/details`);
    return response.data;
  },

  async getCourseProgress(courseSlug: string): Promise<CourseProgressInfo> {
    const response = await apiClient.get(`/labs/linux/${courseSlug}/progress`);
    return response.data;
  },

  async getSessions(skip: number = 0, limit: number = 100): Promise<{ sessions: LabSession[]; total: number }> {
    const response = await apiClient.get(`/labs/linux/sessions?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  async completeCourseTab(courseSlug: string, tabId: string): Promise<any> {
    const response = await apiClient.post(`/labs/linux/progress/${courseSlug}/tabs/${tabId}`);
    return response.data;
  },
};
