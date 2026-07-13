"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/store/auth-store";
import { useRouter } from "next/navigation";
import type { LoginRequest, RegisterRequest } from "@/types/auth";

function storeTokens(tokens: { access_token: string; refresh_token: string }) {
  localStorage.setItem("access_token", tokens.access_token);
  localStorage.setItem("refresh_token", tokens.refresh_token);
}

export function useAuth() {
  const { user, isAuthenticated, setUser, logout } = useAuthStore();
  const queryClient = useQueryClient();
  const router = useRouter();

  const hasToken = typeof window !== "undefined" && !!localStorage.getItem("access_token");

  const { isLoading } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      const u = await authService.me();
      setUser(u);
      return u;
    },
    enabled: hasToken,
    retry: false,
    staleTime: 5 * 60 * 1000,
    meta: { skipErrorToast: true },
  });

  const loginMutation = useMutation({
    mutationFn: (data: LoginRequest) => authService.login(data),
    onSuccess: (tokens) => {
      storeTokens(tokens);
      queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      router.push("/dashboard");
    },
  });

  const registerMutation = useMutation({
    mutationFn: (data: RegisterRequest) => authService.register(data),
    onSuccess: () => {
      // Registration creates inactive user - redirect to plans page
      router.push("/plans");
    },
  });

  return {
    user,
    isAuthenticated,
    isLoading,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout: () => { logout(); queryClient.clear(); router.push("/login"); },
    loginError: loginMutation.error,
    registerError: registerMutation.error,
    isLoggingIn: loginMutation.isPending,
    isRegistering: registerMutation.isPending,
  };
}
