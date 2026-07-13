"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/EmptyState";
import { BarChart3 } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-muted-foreground">Track your proposal performance and metrics</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {["Total Proposals", "Win Rate", "Avg. Bid", "Response Rate"].map((label) => (
          <Card key={label}>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle></CardHeader>
            <CardContent><p className="text-3xl font-bold">—</p></CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader><CardTitle>Proposal Activity</CardTitle></CardHeader>
        <CardContent className="h-64 flex items-center justify-center">
          <EmptyState icon={<BarChart3 className="h-12 w-12" />} title="Analytics coming soon" description="Detailed metrics and charts will appear here once you have proposal activity." />
        </CardContent>
      </Card>
    </div>
  );
}
