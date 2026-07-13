"use client";

import Link from "next/link";
import { FileText, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/EmptyState";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useProposals } from "@/hooks/useProposals";

const statusColors: Record<string, "default" | "secondary" | "success" | "warning" | "outline"> = {
  draft: "secondary",
  under_review: "warning",
  ready_to_submit: "success",
  submitted: "default",
  archived: "outline",
};

export function RecentProposals() {
  const { list } = useProposals();
  const { data, isLoading } = list({ limit: 5 });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Recent Proposals</CardTitle>
        <Link href="/proposals">
          <Button variant="ghost" size="sm">View All <ArrowRight className="ml-1 h-4 w-4" /></Button>
        </Link>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <LoadingSpinner />
        ) : !data?.items.length ? (
          <EmptyState title="No proposals yet" description="Create your first proposal to get started." />
        ) : (
          <div className="space-y-3">
            {data.items.map((p) => (
              <Link key={p.id} href={`/proposals/${p.id}`} className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-accent">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">{p.title || "Untitled Proposal"}</p>
                    <p className="text-xs text-muted-foreground">{p.bid_amount ? `$${p.bid_amount}` : "No bid"} · {new Date(p.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
                <Badge variant={statusColors[p.status] || "secondary"}>{p.status.replace("_", " ")}</Badge>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
