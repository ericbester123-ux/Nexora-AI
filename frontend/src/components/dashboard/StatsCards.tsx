"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, FileText, DollarSign, Target } from "lucide-react";

const stats = [
  { label: "Active Proposals", value: "12", icon: FileText, change: "+2 this week", color: "text-blue-500" },
  { label: "Win Rate", value: "68%", icon: Target, change: "+5% vs last month", color: "text-emerald-500" },
  { label: "Estimated Earnings", value: "$48,500", icon: DollarSign, change: "+$12k this month", color: "text-amber-500" },
  { label: "Opportunity Score", value: "85", icon: TrendingUp, change: "Top 10% of users", color: "text-purple-500" },
];

export function StatsCards() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((s) => (
        <Card key={s.label}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{s.label}</CardTitle>
            <s.icon className={`h-5 w-5 ${s.color}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{s.value}</div>
            <p className="text-xs text-muted-foreground mt-1">{s.change}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
