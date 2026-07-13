"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ConnectionStatusBadge } from "./ConnectionStatusBadge";
import { SyncStatusIndicator } from "./SyncStatusIndicator";
import { Star, ExternalLink, RefreshCw, Loader2, XCircle, AlertCircle, CheckCircle2, Clock } from "lucide-react";
import { toast } from "sonner";
import type { MarketplaceAccount } from "@/types/marketplace";
import { marketplaceService } from "@/services/marketplace.service";

interface ProviderCardProps {
  account: MarketplaceAccount;
  onDisconnected: (accountId: string) => void;
  onSyncComplete: (accountId: string) => void;
}

export function ProviderCard({ account, onDisconnected, onSyncComplete }: ProviderCardProps) {
  const [syncing, setSyncing] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const result = await marketplaceService.sync(account.id);
      toast.success(`Synced: ${result.projects_imported} new, ${result.projects_updated} updated`);
      onSyncComplete(account.id);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || e.message || "Sync failed");
    } finally {
      setSyncing(false);
    }
  };

  const handleDisconnect = async () => {
    setDisconnecting(true);
    try {
      await marketplaceService.disconnect(account.id);
      toast.success("Account disconnected");
      onDisconnected(account.id);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || e.message || "Failed to disconnect");
    } finally {
      setDisconnecting(false);
    }
  };

  const providerName = account.provider === "freelancer" ? "Freelancer.com" : account.provider;
  const connectionStatus = account.is_active
    ? account.sync_status === "error" || account.sync_status === "failed"
      ? "error" as const
      : account.sync_status === "syncing" || account.sync_status === "in_progress"
        ? "syncing" as const
        : "connected" as const
    : "disconnected" as const;

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
            <svg className="h-6 w-6 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" stroke="#00B488" strokeWidth="2" />
              <polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke="#00B488" strokeWidth="2" />
              <line x1="12" y1="22.08" x2="12" y2="12" stroke="#00B488" strokeWidth="2" />
            </svg>
          </div>
          <div>
            <CardTitle className="text-lg">{providerName}</CardTitle>
            <ConnectionStatusBadge status={connectionStatus} />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {account.is_active ? (
          <div className="space-y-3">
            {/* Profile info */}
            <div className="flex items-start gap-4">
              {account.avatar_url ? (
                <img src={account.avatar_url} alt="" className="h-12 w-12 rounded-full object-cover" />
              ) : (
                <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center">
                  <span className="text-lg font-semibold text-muted-foreground">
                    {(account.display_name || account.username || "?")[0].toUpperCase()}
                  </span>
                </div>
              )}
              <div className="space-y-1">
                <p className="font-medium">{account.display_name || account.username || "Connected User"}</p>
                <p className="text-sm text-muted-foreground">@{account.username || account.external_user_id}</p>
                {account.rating && (
                  <div className="flex items-center gap-1 text-sm">
                    <Star className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" />
                    <span>{account.rating.toFixed(1)}</span>
                    {account.reviews_count != null && (
                      <span className="text-muted-foreground">({account.reviews_count} reviews)</span>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 gap-2 text-sm">
              {account.projects_completed != null && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>{account.projects_completed} projects</span>
                </div>
              )}
              {account.verification_status && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  {account.verification_status === "verified" ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-3.5 w-3.5 text-yellow-500" />
                  )}
                  <span>{account.verification_status === "verified" ? "Verified" : "Unverified"}</span>
                </div>
              )}
              {account.connected_at && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Clock className="h-3.5 w-3.5" />
                  <span>Connected {new Date(account.connected_at).toLocaleDateString()}</span>
                </div>
              )}
              {account.profile_url && (
                <div className="flex items-center gap-1.5">
                  <a href={account.profile_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-primary hover:underline">
                    <ExternalLink className="h-3.5 w-3.5" />
                    View Profile
                  </a>
                </div>
              )}
            </div>

            {/* Sync status */}
            <SyncStatusIndicator
              status={account.sync_status}
              lastSyncAt={account.last_sync_at}
              errorMessage={account.sync_error_message}
            />

            {/* Actions */}
            <div className="flex gap-2 pt-1">
              <Button variant="default" size="sm" onClick={handleSync} disabled={syncing}>
                {syncing ? <Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-1.5" />}
                Sync Now
              </Button>
              <Button variant="destructive" size="sm" onClick={handleDisconnect} disabled={disconnecting}>
                {disconnecting ? <Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> : <XCircle className="h-4 w-4 mr-1.5" />}
                Disconnect
              </Button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">This account has been disconnected.</p>
        )}
      </CardContent>
    </Card>
  );
}
