"use client";

import { useState, useEffect } from "react";
import { marketplaceService } from "@/services/marketplace.service";
import { ProviderCard } from "@/components/marketplace/ProviderCard";
import { ConnectProviderModal } from "@/components/marketplace/ConnectProviderModal";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Plug, Plus, Loader2 } from "lucide-react";
import type { MarketplaceAccount } from "@/types/marketplace";

export default function ConnectionsPage() {
  const [accounts, setAccounts] = useState<MarketplaceAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showConnectModal, setShowConnectModal] = useState(false);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await marketplaceService.getAccounts();
      setAccounts(data);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e.message || "Failed to load accounts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleConnected = (result: any) => {
    fetchAccounts();
  };

  const handleDisconnected = (accountId: string) => {
    setAccounts((prev) => prev.filter((a) => a.id !== accountId));
  };

  const handleSyncComplete = (accountId: string) => {
    fetchAccounts();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Connected Accounts</h1>
          <p className="text-muted-foreground">Manage your marketplace connections</p>
        </div>
        <Button onClick={() => setShowConnectModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Connect Account
        </Button>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchAccounts} />
      ) : accounts.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Plug className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No accounts connected</h3>
            <p className="text-sm text-muted-foreground text-center max-w-md mb-6">
              Connect your Freelancer.com account to start syncing projects and generating AI-powered proposals.
            </p>
            <Button onClick={() => setShowConnectModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Connect Your First Account
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {accounts.map((account) => (
            <ProviderCard
              key={account.id}
              account={account}
              onDisconnected={handleDisconnected}
              onSyncComplete={handleSyncComplete}
            />
          ))}
        </div>
      )}

      <ConnectProviderModal
        open={showConnectModal}
        onOpenChange={setShowConnectModal}
        provider="freelancer"
        onConnected={handleConnected}
      />
    </div>
  );
}
