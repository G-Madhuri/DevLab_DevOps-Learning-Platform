import { apiClient, setTokens, clearTokens, getRefreshToken } from "@/lib/api-client";
import { AuthResponse, User } from "@/types";

export const authService = {
  async register(data: any): Promise<User> {
    const response = await apiClient.post("/auth/register", data);
    return response.data;
  },

  async login(data: any): Promise<AuthResponse> {
    const response = await apiClient.post("/auth/login", data);
    const authData: AuthResponse = response.data;
    setTokens(authData.access_token, authData.refresh_token);
    return authData;
  },

  async logout(): Promise<void> {
    const refreshToken = getRefreshToken();
    try {
      if (refreshToken) {
        await apiClient.post("/auth/logout", { refresh_token: refreshToken });
      }
    } finally {
      clearTokens();
    }
  },

  async getMe(): Promise<User> {
    const response = await apiClient.get("/users/me");
    return response.data;
  },

  async updateMe(data: any): Promise<User> {
    const response = await apiClient.put("/users/me", data);
    return response.data;
  },
};
