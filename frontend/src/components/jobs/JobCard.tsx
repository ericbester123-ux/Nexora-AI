"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MapPin, Clock, DollarSign, TrendingUp } from "lucide-react";
import type { Opportunity } from "@/types/api";

export function JobCard({ job }: { job: Opportunity }) {
  return (
    <Card className="transition-all hover:shadow-md">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">{job.title}</CardTitle>
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{job.description}</p>
          </div>
          {job.score !== undefined && (
            <Badge variant={job.score >= 80 ? "success" : job.score >= 60 ? "warning" : "secondary"} className="ml-2">
              <TrendingUp className="mr-1 h-3 w-3" /> {job.score}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-3 text-sm text-muted-foreground mb-3">
          {job.budget_min && job.budget_max && (
            <span className="flex items-center gap-1">
              <DollarSign className="h-4 w-4" /> ${job.budget_min.toLocaleString()} - ${job.budget_max.toLocaleString()}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Clock className="h-4 w-4" /> {job.status}
          </span>
          {job.category && <span className="flex items-center gap-1"><MapPin className="h-4 w-4" /> {job.category}</span>}
        </div>
        {job.skills && job.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {job.skills.map((s) => <Badge key={s} variant="secondary" className="text-xs">{s}</Badge>)}
          </div>
        )}
        <Button variant="outline" size="sm" className="w-full">View Details</Button>
      </CardContent>
    </Card>
  );
}
