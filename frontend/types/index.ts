export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
  streak?: number;
}

export interface UserSimple {
  id: string;
  email: string;
  name: string;
  streak?: number;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserSimple;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Lab {
  id: string;
  title: string;
  slug: string;
  description: string;
  difficulty: string;
  duration: string;
  category: string;
  icon: string;
  estimated_time: string;
  status: string;
  coming_soon: boolean;
}

export interface LabListResponse {
  labs: Lab[];
  total: number;
}
