"use client";

import { useState } from "react";
import { useJobs } from "@/hooks/useJobs";
import { JobCard } from "@/components/jobs/JobCard";
import { JobFilters } from "@/components/jobs/JobFilters";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { ErrorState } from "@/components/shared/ErrorState";
import { Briefcase, ChevronLeft, ChevronRight } from "lucide-react";

export default function JobsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useJobs({
    search: search || undefined,
    status: status !== "all" ? status : undefined,
    page,
    size: 12,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Jobs</h1>
        <p className="text-muted-foreground">Browse and find your next opportunity</p>
      </div>
      <JobFilters search={search} onSearchChange={(v) => { setSearch(v); setPage(1); }} status={status} onStatusChange={(v) => { setStatus(v); setPage(1); }} />
      {isLoading ? <LoadingSpinner /> : error ? <ErrorState message="Failed to load jobs" onRetry={refetch} /> : data?.items?.length ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.items.map((job) => <JobCard key={job.id} job={job} />)}
          </div>
          <div className="flex items-center justify-between pt-4">
            <p className="text-sm text-muted-foreground">Showing {data.items.length} of {data.total} opportunities</p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                <ChevronLeft className="h-4 w-4" /> Previous
              </Button>
              <Button variant="outline" size="sm" disabled={page * 12 >= data.total} onClick={() => setPage((p) => p + 1)}>
                Next <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </>
      ) : (
        <EmptyState icon={<Briefcase className="h-12 w-12" />} title="No jobs found" description="Try adjusting your search or filters." />
      )}
    </div>
  );
}
