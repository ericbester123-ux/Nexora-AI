export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  freelancer_user_id: string | null;
  freelancer_oauth_token: string | null;
  freelancer_refresh_token: string | null;
  freelancer_token_expires_at: string | null;
  freelancer_connected_at: string | null;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}
