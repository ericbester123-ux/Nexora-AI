"use client";

import { StatsCards } from "@/components/dashboard/StatsCards";
import { RecentProposals } from "@/components/dashboard/RecentProposals";
import { ActivityTimeline } from "@/components/dashboard/ActivityTimeline";
import { OpportunityScore } from "@/components/dashboard/OpportunityScore";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <StatsCards />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2"><RecentProposals /></div>
        <OpportunityScore />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <ActivityTimeline />
      </div>
    </div>
  );
}
