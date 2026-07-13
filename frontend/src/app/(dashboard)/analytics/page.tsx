"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { BarChart3, TrendingUp, DollarSign, Target, Briefcase, Eye, CheckCircle2, XCircle, RefreshCw } from "lucide-react";
import { marketplaceService } from "@/services/marketplace.service";
import type { MarketplaceAccount, MarketplaceProviderStats } from "@/types/marketplace";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function AnalyticsPage() {
  const [accounts, setAccounts] = useState<MarketplaceAccount[]>([]);
  const [stats, setStats] = useState<Record<string, MarketplaceProviderStats>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const accts = await marketplaceService.getAccounts();
        setAccounts(accts);
        const statsMap: Record<string, MarketplaceProviderStats> = {};
        for (const acct of accts) {
          try {
            statsMap[acct.id] = await marketplaceService.getStats(acct.id);
          } catch {}
        }
        setStats(statsMap);
      } catch {
        // No accounts
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading) return <LoadingSpinner />;

  if (accounts.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">Track your proposal performance and metrics</p>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No data yet</h3>
            <p className="text-sm text-muted-foreground text-center max-w-md mb-6">
              Connect a marketplace account and sync projects to see your analytics.
            </p>
            <Link href="/settings/connections">
              <Button variant="outline">Connect Account</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Aggregate stats across all accounts
  const total: MarketplaceProviderStats = Object.values(stats).reduce(
    (acc, s) => ({
      ...s,
      total_projects_imported: acc.total_projects_imported + s.total_projects_imported,
      projects_viewed: acc.projects_viewed + s.projects_viewed,
      proposals_generated: acc.proposals_generated + s.proposals_generated,
      proposals_submitted: acc.proposals_submitted + s.proposals_submitted,
      projects_won: acc.projects_won + s.projects_won,
      projects_lost: acc.projects_lost + s.projects_lost,
      average_bid_amount: acc.average_bid_amount + s.average_bid_amount,
    }),
    {
      provider: "all",
      total_projects_imported: 0,
      projects_viewed: 0,
      proposals_generated: 0,
      proposals_submitted: 0,
      projects_won: 0,
      projects_lost: 0,
      win_rate: 0,
      average_bid_amount: 0,
      total_syncs: 0,
      last_sync_at: null,
      last_sync_status: null,
    }
  );

  const totalDecided = total.projects_won + total.projects_lost;
  const winRate = totalDecided > 0 ? Math.round((total.projects_won / totalDecided) * 100) : 0;
  const avgBid = Object.values(stats).length > 0
    ? total.average_bid_amount / Object.values(stats).length
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">Track your marketplace performance and metrics</p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Projects Imported</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent><p className="text-3xl font-bold">{total.total_projects_imported}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Win Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent><p className="text-3xl font-bold">{winRate}%</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg. Bid</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent><p className="text-3xl font-bold">${avgBid.toFixed(0)}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">Proposals</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent><p className="text-3xl font-bold">{total.proposals_generated}</p></CardContent>
        </Card>
      </div>

      {/* Per-provider breakdown */}
      <div className="grid gap-6 lg:grid-cols-2">
        {Object.entries(stats).map(([accountId, s]) => {
          const account = accounts.find((a) => a.id === accountId);
          const providerWinRate = (s.projects_won + s.projects_lost) > 0
            ? Math.round((s.projects_won / (s.projects_won + s.projects_lost)) * 100)
            : 0;

          return (
            <Card key={accountId}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base capitalize flex items-center gap-2">
                  <Briefcase className="h-4 w-4" />
                  {account?.display_name || account?.username || s.provider}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Projects</p>
                    <p className="text-xl font-semibold">{s.total_projects_imported}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Viewed</p>
                    <p className="text-xl font-semibold">{s.projects_viewed}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Won</p>
                    <p className="text-xl font-semibold text-green-600">{s.projects_won}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Lost</p>
                    <p className="text-xl font-semibold text-red-600">{s.projects_lost}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Win Rate</p>
                    <p className="text-xl font-semibold">{providerWinRate}%</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Avg Bid</p>
                    <p className="text-xl font-semibold">${s.average_bid_amount.toFixed(0)}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
