"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Target } from "lucide-react";

const score = 85;
const breakdown = [
  { label: "Experience Match", value: 90 },
  { label: "Budget Alignment", value: 80 },
  { label: "Timeline Fit", value: 75 },
  { label: "Competition Analysis", value: 95 },
];

export function OpportunityScore() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Target className="h-5 w-5 text-primary" /> Opportunity Score
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center mb-4">
          <div className="text-4xl font-bold text-primary">{score}</div>
          <p className="text-sm text-muted-foreground">out of 100</p>
        </div>
        <div className="space-y-3">
          {breakdown.map((b) => (
            <div key={b.label}>
              <div className="flex justify-between text-sm mb-1">
                <span>{b.label}</span>
                <span className="text-muted-foreground">{b.value}%</span>
              </div>
              <Progress value={b.value} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
