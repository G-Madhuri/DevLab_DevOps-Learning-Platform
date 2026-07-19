import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Storage helper functions
export const getAccessToken = () => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("access_token");
  }
  return null;
};

export const getRefreshToken = () => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("refresh_token");
  }
  return null;
};

export const setTokens = (accessToken: string, refreshToken: string) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
  }
};

export const clearTokens = () => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }
};

// Request Interceptor: Inject Access Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Flag to prevent infinite loops of token refreshes
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: string | PromiseLike<string>) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token);
    } else {
      prom.reject(error);
    }
  });
  failedQueue = [];
};

// Response Interceptor: Catch 401 & Auto-Refresh Token + Offline Demo Fallback
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    if (!originalRequest) return Promise.reject(error);

    // Dynamic Client-side Mock Fallback (Demo Mode) when Backend is Offline
    if (error.message === "Network Error" || !error.response) {
      const url = originalRequest.url || "";
      console.warn(`[DevLab Demo Mode] Backend unreachable. Mocking endpoint: ${url}`);

      if (url.includes("/users/me")) {
        return Promise.resolve({
          data: {
            id: "00000000-0000-0000-0000-000000000000",
            email: "google.user@devlab.com",
            name: "Google Learner",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          status: 200,
          statusText: "OK",
          headers: {},
          config: originalRequest,
        });
      }

      if (url.includes("/auth/login")) {
        return Promise.resolve({
          data: {
            access_token: "mock-access-token",
            refresh_token: "mock-refresh-token",
            token_type: "bearer",
            user: {
              id: "00000000-0000-0000-0000-000000000000",
              email: "google.user@devlab.com",
              name: "Google Learner",
            },
          },
          status: 200,
          statusText: "OK",
          headers: {},
          config: originalRequest,
        });
      }

      if (url.includes("/auth/register")) {
        return Promise.resolve({
          data: {
            id: "00000000-0000-0000-0000-000000000000",
            email: "google.user@devlab.com",
            name: "Google Learner",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          status: 201,
          statusText: "Created",
          headers: {},
          config: originalRequest,
        });
      }

      if (url.includes("/labs/categories")) {
        return Promise.resolve({
          data: ["Linux", "Docker", "Kubernetes", "Git", "GitHub Actions", "CI/CD", "Jenkins", "Terraform", "Ansible", "AWS", "Azure"],
          status: 200,
          statusText: "OK",
          headers: {},
          config: originalRequest,
        });
      }

      if (url.match(/\/labs\/[a-zA-Z0-9-]+$/)) {
        const slug = url.split("/labs/")[1];
        const title = slug
          .split("-")
          .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
          .join(" ");

        return Promise.resolve({
          data: {
            id: "00000000-0000-0000-0000-000000000000",
            title: title,
            slug: slug,
            description: `An interactive simulated playground designed to guide you through ${title} core commands and practices.`,
            difficulty: "Intermediate",
            duration: "45 minutes",
            category: slug.includes("docker") ? "Docker" : slug.includes("kubernetes") ? "Kubernetes" : "Linux",
            icon: "terminal",
            estimated_time: "45m",
            status: "Beta",
            coming_soon: true,
          },
          status: 200,
          statusText: "OK",
          headers: {},
          config: originalRequest,
        });
      }

      if (url.includes("/labs")) {
        return Promise.resolve({
          data: {
            labs: [
              {
                id: "1",
                title: "Linux Command Line Basics",
                slug: "linux-command-line-basics",
                description: "Master files navigation, path routing, standard inputs/outputs, and piping commands.",
                difficulty: "Beginner",
                duration: "30 minutes",
                category: "Linux",
                icon: "terminal",
                estimated_time: "30m",
                status: "Beta",
                coming_soon: true,
              },
              {
                id: "2",
                title: "Docker Fundamentals",
                slug: "docker-fundamentals",
                description: "Introduction to container runtimes, pull operations, port mapping, and volume configurations.",
                difficulty: "Beginner",
                duration: "45 minutes",
                category: "Docker",
                icon: "box",
                estimated_time: "45m",
                status: "Active",
                coming_soon: true,
              },
              {
                id: "3",
                title: "Kubernetes Pods & Deployments",
                slug: "kubernetes-pods-and-deployments",
                description: "Deploy pods, manage replica counts, and perform rolling updates with custom YAML configurations.",
                difficulty: "Beginner",
                duration: "60 minutes",
                category: "Kubernetes",
                icon: "layers",
                estimated_time: "60m",
                status: "Active",
                coming_soon: true,
              },
              {
                id: "4",
                title: "Terraform Basics",
                slug: "terraform-basics",
                description: "Learn initializations, dry-run plans, applying configurations, and managing variables.",
                difficulty: "Beginner",
                duration: "45 minutes",
                category: "Terraform",
                icon: "cpu",
                estimated_time: "45m",
                status: "Active",
                coming_soon: true,
              },
            ],
            total: 4,
          },
          status: 200,
          statusText: "OK",
          headers: {},
          config: originalRequest,
        });
      }
    }

    // Standard 401 Handling & Token Refresh
    const isAuthRoute =
      originalRequest.url?.includes("/auth/login") ||
      originalRequest.url?.includes("/auth/register");

    if (error.response?.status === 401 && !isAuthRoute) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      isRefreshing = true;
      const refreshToken = getRefreshToken();

      if (!refreshToken) {
        clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token: new_refresh_token } = response.data;
        setTokens(access_token, new_refresh_token);

        processQueue(null, access_token);
        isRefreshing = false;

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
