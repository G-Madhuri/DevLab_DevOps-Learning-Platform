import { apiClient } from "@/lib/api-client";
import { Lab, LabListResponse } from "@/types";

export const labService = {
  async listLabs(params?: {
    search?: string;
    difficulty?: string;
    category?: string;
    sort_by?: string;
    skip?: number;
    limit?: number;
  }): Promise<LabListResponse> {
    const response = await apiClient.get("/labs", { params });
    return response.data;
  },

  async getLabBySlug(slug: string): Promise<Lab> {
    const response = await apiClient.get(`/labs/${slug}`);
    return response.data;
  },

  async getCategories(): Promise<string[]> {
    const response = await apiClient.get("/labs/categories");
    return response.data;
  },

  async listAcademies(): Promise<any[]> {
    const response = await apiClient.get("/labs/academies/list");
    return response.data;
  },

  async generateCertificate(academyId: string): Promise<any> {
    const response = await apiClient.post(`/labs/academies/detail/${academyId}/certificate/generate`);
    return response.data;
  },
};
