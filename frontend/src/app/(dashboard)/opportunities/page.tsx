"use client";

import { useState } from "react";
import Link from "next/link";
import { useProposals } from "@/hooks/useProposals";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { FileText, Plus, Search, ArrowRight } from "lucide-react";

const statusColors: Record<string, "default" | "secondary" | "success" | "warning" | "outline"> = {
  draft: "secondary",
  under_review: "warning",
  ready_to_submit: "success",
  submitted: "default",
  archived: "outline",
};

export default function OpportunitiesPage() {
  const [statusFilter, setStatusFilter] = useState("all");
  const [search, setSearch] = useState("");
  const { list } = useProposals();
  const { data, isLoading, error, refetch } = list();

  const filtered = data?.items?.filter((p) => {
    if (statusFilter !== "all" && p.status !== statusFilter) return false;
    if (search && !p.title?.toLowerCase().includes(search.toLowerCase()) && !p.cover_letter?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  }) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Proposals</h1>
          <p className="text-muted-foreground">Manage and track your proposals</p>
        </div>
        <Button asChild>
          <Link href="/jobs"><Plus className="mr-2 h-4 w-4" /> New Proposal</Link>
        </Button>
      </div>
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search proposals..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="All Statuses" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="under_review">Under Review</SelectItem>
            <SelectItem value="ready_to_submit">Ready to Submit</SelectItem>
            <SelectItem value="submitted">Submitted</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>
      </div>
      {isLoading ? <LoadingSpinner /> : error ? <ErrorState message="Failed to load proposals" onRetry={refetch} /> : filtered.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((p) => (
            <Link key={p.id} href={`/proposals/${p.id}`}>
              <Card className="transition-all hover:shadow-md h-full">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-base">{p.title || "Untitled"}</CardTitle>
                    <Badge variant={statusColors[p.status] || "secondary"}>{p.status.replace("_", " ")}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{p.cover_letter || "No description"}</p>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{p.bid_amount ? `$${p.bid_amount.toLocaleString()}` : "No bid"}</span>
                    <span className="flex items-center text-primary">
                      Review <ArrowRight className="ml-1 h-4 w-4" />
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState icon={<FileText className="h-12 w-12" />} title="No proposals found" description="Create your first proposal to get started." action={<Button asChild><Link href="/jobs">Browse Jobs</Link></Button>} />
      )}
    </div>
  );
}
