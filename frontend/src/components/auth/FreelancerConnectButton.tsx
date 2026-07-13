"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

interface FreelancerOAuthProps {
  onConnect?: (freelancerUserId: string) => void;
}

export function FreelancerConnectButton({ onConnect }: FreelancerOAuthProps) {
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleConnect = useCallback(async () => {
    try {
      setIsLoading(true);
      
      // 1. Get the auth URL from backend
      const res = await fetch("/api/integrations/freelancer/auth-url", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to get auth URL");
      }

      const { auth_url, state } = await res.json();

      // 2. Open popup
      const popup = window.open(
        auth_url,
        "freelancer_oauth",
        "width=600,height=700,scrollbars=yes,resizable=yes"
      );

      if (!popup) {
        throw new Error("Popup blocked. Please allow popups for this site.");
      }

      // 3. Listen for callback message
      const messageHandler = async (event: MessageEvent) => {
        // Verify origin
        if (event.origin !== window.location.origin) return;

        if (event.data.type === "FREELANCER_OAUTH_CALLBACK") {
          window.removeEventListener("message", messageHandler);
          
          if (event.data.error) {
            toast.error(event.data.error_description || "Authentication failed");
            return;
          }

          if (!event.data.code || !event.data.state) {
            toast.error("Invalid callback data");
            return;
          }

          try {
            // Exchange code for token
            const tokenRes = await fetch("/api/integrations/freelancer/exchange-code", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("access_token")}`,
              },
              body: JSON.stringify({
                code: event.data.code,
                state: event.data.state,
              }),
            });

            if (!tokenRes.ok) {
              const data = await tokenRes.json();
              throw new Error(data.detail || "Failed to exchange code");
            }

            const data = await tokenRes.json();
            toast.success(data.message);
            
            if (onConnect && data.freelancer_user_id) {
              onConnect(data.freelancer_user_id);
            }

            // Refresh user data
            const userRes = await fetch("/api/auth/me", {
              headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
            });
            if (userRes.ok) {
              const userData = await userRes.json();
              // The auth store will be updated via the auth provider
              window.location.reload();
            }
          } catch (e: any) {
            toast.error(e.message);
          }
        }
      };

      window.addEventListener("message", messageHandler);

      // Cleanup if popup is closed manually
      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          window.removeEventListener("message", messageHandler);
        }
      }, 500);

    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setIsLoading(false);
    }
  }, [onConnect]);

  return (
    <button
      onClick={handleConnect}
      disabled={isLoading}
      className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors"
    >
      <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="#00B488" strokeWidth="2" />
        <polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke="#00B488" strokeWidth="2" />
        <line x1="12" y1="22.08" x2="12" y2="12" stroke="#00B488" strokeWidth="2" />
      </svg>
      <span>Connect Freelancer</span>
    </button>
  );
}

export function FreelancerOAuthPopup() {
  // This component is rendered in the popup window
  // It handles the OAuth callback and communicates with the parent window
  return null;
}