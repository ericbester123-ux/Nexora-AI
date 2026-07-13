"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Clock, CheckCircle2, Edit3, Send, Archive } from "lucide-react";
import { EmptyState } from "@/components/shared/EmptyState";

const activities = [
  { icon: Send, text: "Proposal for Website Redesign submitted", time: "2 hours ago", color: "text-blue-500" },
  { icon: CheckCircle2, text: "Proposal marked as Ready to Submit", time: "1 day ago", color: "text-emerald-500" },
  { icon: Edit3, text: "Edited proposal - updated pricing", time: "2 days ago", color: "text-amber-500" },
  { icon: Archive, text: "Archived old proposal draft", time: "3 days ago", color: "text-muted-foreground" },
];

export function ActivityTimeline() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Activity Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((a, i) => (
            <div key={i} className="flex gap-3">
              <div className="flex flex-col items-center">
                <div className={`rounded-full border p-1.5 ${a.color}`}>
                  <a.icon className="h-3.5 w-3.5" />
                </div>
                {i < activities.length - 1 && <div className="mt-1 h-full w-px bg-border" />}
              </div>
              <div className="pb-4">
                <p className="text-sm">{a.text}</p>
                <p className="text-xs text-muted-foreground">{a.time}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
