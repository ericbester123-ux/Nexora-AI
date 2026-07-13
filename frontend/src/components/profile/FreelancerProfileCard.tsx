"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, CheckCircle2, XCircle, Loader2, RefreshCw, Briefcase } from "lucide-react";
import { toast } from "sonner";
import { marketplaceService } from "@/services/marketplace.service";
import type { MarketplaceAccount } from "@/types/marketplace";

function StarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}

function ShieldCheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

function LogInIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
      <polyline points="10 17 15 12 10 7" />
      <line x1="15" x2="3" y1="12" y2="12" />
    </svg>
  );
}

export function FreelancerProfileCard() {
  const [account, setAccount] = useState<MarketplaceAccount | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [connecting, setConnecting] = useState(false);

  const fetchAccount = useCallback(async () => {
    try {
      setLoading(true);
      const accounts = await marketplaceService.getAccounts();
      setAccount(accounts.find((a) => a.provider === "freelancer") || null);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAccount();
  }, [fetchAccount]);

  const isConnected = !!(account?.external_user_id && account?.has_valid_token);

  const handleOAuth = useCallback(async () => {
    try {
      setConnecting(true);
      const { auth_url, state } = await marketplaceService.getAuthUrl("freelancer");

      const popup = window.open(
        auth_url,
        "freelancer_oauth",
        "width=600,height=700,scrollbars=yes,resizable=yes"
      );

      if (!popup) {
        toast.error("Popup blocked. Please allow popups for this site.");
        return;
      }

      const messageHandler = async (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;

        if (event.data.type === "FREELANCER_OAUTH_CALLBACK" || event.data.type === "MARKETPLACE_OAUTH_CALLBACK") {
          window.removeEventListener("message", messageHandler);

          if (event.data.error) {
            toast.error(event.data.error_description || "Authentication failed");
            return;
          }

          if (!event.data.code) {
            toast.error("Invalid callback data");
            return;
          }

          try {
            const redirectUri = `${window.location.origin}/api/integrations/freelancer/callback`;
            const result = await marketplaceService.exchangeCode("freelancer", event.data.code, state, redirectUri);
            toast.success(result.message);
            await fetchAccount();
          } catch (e: any) {
            toast.error(e?.response?.data?.detail || e.message || "Failed to connect");
          }
        }
      };

      window.addEventListener("message", messageHandler);

      const checkClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(checkClosed);
          window.removeEventListener("message", messageHandler);
        }
      }, 500);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || e.message || "Failed to start connection");
    } finally {
      setConnecting(false);
    }
  }, [fetchAccount]);

  const handleSync = async () => {
    if (!account) return;
    setSyncing(true);
    try {
      const result = await marketplaceService.sync(account.id);
      toast.success(`${result.projects_imported} new, ${result.projects_updated} updated`);
      await fetchAccount();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || e.message || "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    if (!account) return;
    try {
      await marketplaceService.disconnect(account.id);
      toast.success("Freelancer account disconnected.");
      setAccount(null);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || e.message || "Failed to disconnect");
    }
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
          <svg className="h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="#00B488" strokeWidth="2" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke="#00B488" strokeWidth="2" />
            <line x1="12" y1="22.08" x2="12" y2="12" stroke="#00B488" strokeWidth="2" />
          </svg>
        </div>
        <div>
          <CardTitle className="text-lg">Freelancer.com</CardTitle>
          <p className="text-sm text-muted-foreground">
            {loading
              ? "Checking connection..."
              : isConnected
                ? "Connected — syncing projects and profile data"
                : "Not connected"}
          </p>
        </div>
        {!loading && isConnected && (
          <Badge variant="outline" className="ml-auto bg-green-50 text-green-700 border-green-200">
            <CheckCircle2 className="h-3 w-3 mr-1" />
            Connected
          </Badge>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {loading && (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {!loading && isConnected && account && (
          <>
            <div className="flex items-center gap-3 p-3 bg-muted/30 rounded-lg">
              <Avatar className="h-12 w-12">
                <AvatarImage src={account.avatar_url || undefined} />
                <AvatarFallback className="bg-primary/10 text-primary">
                  {account.display_name?.[0]?.toUpperCase() || "F"}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{account.display_name || "Freelancer User"}</p>
                <p className="text-sm text-muted-foreground truncate">{account.email || account.username || account.external_user_id}</p>
                {account.rating && (
                  <div className="flex items-center gap-1 text-sm text-amber-500 mt-0.5">
                    <StarIcon className="h-3 w-3" />
                    <span>{account.rating.toFixed(1)}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              {account.projects_completed != null && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Briefcase className="h-4 w-4" />
                  <span>{account.projects_completed} projects completed</span>
                </div>
              )}
              {account.verification_status && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <ShieldCheckIcon className="h-4 w-4" />
                  <span className="capitalize">{account.verification_status}</span>
                </div>
              )}
              {account.profile_url && (
                <div className="flex items-center gap-2 text-muted-foreground col-span-2">
                  <ExternalLink className="h-4 w-4" />
                  <a href={account.profile_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline truncate">
                    View Freelancer Profile
                  </a>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={handleSync} disabled={syncing}>
                {syncing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Sync Now
              </Button>
              <Button variant="destructive" size="sm" onClick={handleDisconnect}>
                <XCircle className="h-4 w-4 mr-1" />
                Disconnect
              </Button>
            </div>
          </>
        )}

        {!loading && !isConnected && (
          <div className="text-center py-4">
            <Button onClick={handleOAuth} disabled={connecting} size="lg" className="w-full">
              {connecting ? (
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              ) : (
                <LogInIcon className="h-5 w-5 mr-2" />
              )}
              Sign in with Freelancer
            </Button>
            <p className="text-xs text-muted-foreground mt-3">
              Authorize Nexora AI to access your Freelancer profile, projects, and bids.
              All data is synced automatically and kept up to date.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
