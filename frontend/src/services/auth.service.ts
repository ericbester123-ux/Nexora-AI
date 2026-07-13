import { api } from "@/lib/api";
import type { AuthTokens, LoginRequest, RegisterRequest, User } from "@/types/auth";

export const authService = {
  async login(data: LoginRequest): Promise<AuthTokens> {
    const res = await api.post("/auth/login", { email: data.email, password: data.password });
    return res.data;
  },

  async register(data: RegisterRequest): Promise<AuthTokens> {
    const res = await api.post("/auth/register", data);
    return res.data;
  },

  async me(): Promise<User> {
    const res = await api.get("/auth/me");
    return res.data;
  },

  async refresh(refreshToken: string): Promise<AuthTokens> {
    const res = await api.post("/auth/refresh", { refresh_token: refreshToken });
    return res.data;
  },
};
