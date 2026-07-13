"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Plug, RefreshCw, Loader2, Briefcase, TrendingUp, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { marketplaceService } from "@/services/marketplace.service";

interface SyncStatus {
  account_id: string;
  provider: string;
  sync_status: string;
  last_sync_at: string | null;
  sync_error_message: string | null;
}

export function MarketplaceDashboardCard() {
  const [syncStatuses, setSyncStatuses] = useState<SyncStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const fetchStatus = async () => {
    try {
      const data = await marketplaceService.getSyncStatus();
      setSyncStatuses(data);
    } catch {
      // No accounts connected - not an error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader><CardTitle>Marketplace Connections</CardTitle></CardHeader>
        <CardContent><LoadingSpinner /></CardContent>
      </Card>
    );
  }

  if (syncStatuses.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plug className="h-5 w-5" />
            Marketplace Connections
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-8 text-center">
          <Plug className="h-10 w-10 text-muted-foreground mb-3" />
          <p className="text-sm font-medium mb-1">No marketplace connected</p>
          <p className="text-xs text-muted-foreground mb-4">Connect to sync projects automatically</p>
          <Link href="/settings/connections">
            <Button variant="outline" size="sm">Connect Account</Button>
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Plug className="h-5 w-5" />
          Marketplace Connections
        </CardTitle>
        <Link href="/settings/connections">
          <Button variant="ghost" size="sm">Manage</Button>
        </Link>
      </CardHeader>
      <CardContent className="space-y-3">
        {syncStatuses.map((status) => (
          <div key={status.account_id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Briefcase className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium capitalize">{status.provider}</p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  {status.sync_status === "healthy" || status.sync_status === "completed" ? (
                    <span className="flex items-center gap-1 text-green-600">
                      <CheckCircle2 className="h-3 w-3" /> Healthy
                    </span>
                  ) : status.sync_status === "error" || status.sync_status === "failed" ? (
                    <span className="flex items-center gap-1 text-red-600">
                      <span className="h-2 w-2 rounded-full bg-red-500" /> Error
                    </span>
                  ) : status.sync_status === "syncing" ? (
                    <span className="flex items-center gap-1 text-blue-600">
                      <Loader2 className="h-3 w-3 animate-spin" /> Syncing
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-gray-500">
                      <span className="h-2 w-2 rounded-full bg-gray-400" /> Never synced
                    </span>
                  )}
                  {status.last_sync_at && (
                    <>
                      <span>·</span>
                      <span>Last: {new Date(status.last_sync_at).toLocaleDateString()}</span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
