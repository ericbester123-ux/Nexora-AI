"use client";

import { useState, useEffect, useCallback } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { marketplaceService } from "@/services/marketplace.service";

interface ConnectProviderModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  provider: string;
  onConnected: (result: any) => void;
}

export function ConnectProviderModal({ open, onOpenChange, provider, onConnected }: ConnectProviderModalProps) {
  const [isConnecting, setIsConnecting] = useState(false);
  const [step, setStep] = useState<"init" | "waiting" | "exchanging">("init");

  const providerName = provider === "freelancer" ? "Freelancer.com" : provider;

  const handleConnect = useCallback(async () => {
    try {
      setIsConnecting(true);

      // Get the auth URL
      const { auth_url, state } = await marketplaceService.getAuthUrl(provider);

      // Open popup
      const popup = window.open(
        auth_url,
        `${provider}_oauth`,
        "width=600,height=700,scrollbars=yes,resizable=yes"
      );

      if (!popup) {
        toast.error("Popup blocked. Please allow popups for this site.");
        return;
      }

      setStep("waiting");

      // Listen for callback
      const messageHandler = async (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;

        if (event.data.type === "FREELANCER_OAUTH_CALLBACK" || 
            (event.data.type === "MARKETPLACE_OAUTH_CALLBACK" && event.data.provider === provider)) {
          window.removeEventListener("message", messageHandler);

          if (event.data.error) {
            toast.error(event.data.error_description || "Authentication failed");
            setStep("init");
            return;
          }

          if (!event.data.code) {
            toast.error("Invalid callback data");
            setStep("init");
            return;
          }

          setStep("exchanging");

          try {
            const redirectUri = `${window.location.origin}/api/integrations/freelancer/callback`;
            const result = await marketplaceService.exchangeCode(provider, event.data.code, state, redirectUri);
            toast.success(result.message);
            onConnected(result);
            onOpenChange(false);
          } catch (e: any) {
            toast.error(e?.response?.data?.detail || e.message || "Failed to connect");
          } finally {
            setStep("init");
          }
        }
      };

      window.addEventListener("message", messageHandler);

      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          window.removeEventListener("message", messageHandler);
          if (step !== "exchanging") {
            setStep("init");
          }
        }
      }, 500);

    } catch (e: any) {
      toast.error(e?.response?.data?.detail || e.message || "Failed to start connection");
    } finally {
      setIsConnecting(false);
    }
  }, [provider, onConnected, onOpenChange, step]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Connect {providerName}</DialogTitle>
          <DialogDescription>
            Connect your {providerName} account to sync projects and generate AI-powered proposals.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="flex items-center justify-center">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
              <svg className="h-8 w-8 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="#00B488" strokeWidth="2" />
                <polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke="#00B488" strokeWidth="2" />
                <line x1="12" y1="22.08" x2="12" y2="12" stroke="#00B488" strokeWidth="2" />
              </svg>
            </div>
          </div>
          <div className="text-center text-sm text-muted-foreground">
            {step === "init" && (
              <p>Click the button below to authorize Nexora AI to access your {providerName} account.</p>
            )}
            {step === "waiting" && (
              <p className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Waiting for authorization...
              </p>
            )}
            {step === "exchanging" && (
              <p className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Completing connection...
              </p>
            )}
          </div>
          <div className="text-xs text-muted-foreground space-y-1">
            <p className="font-medium text-foreground">What will be shared:</p>
            <ul className="list-disc list-inside space-y-0.5">
              <li>Your public profile information</li>
              <li>Access to browse and sync projects</li>
              <li>Ability to submit proposals on your behalf (only after your approval)</li>
            </ul>
          </div>
        </div>
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={step !== "init"}>
            Cancel
          </Button>
          <Button onClick={handleConnect} disabled={isConnecting || step !== "init"}>
            {isConnecting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <ExternalLink className="h-4 w-4 mr-2" />}
            Connect {providerName}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
