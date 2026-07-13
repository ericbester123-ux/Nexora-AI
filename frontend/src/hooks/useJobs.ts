"use client";

import { useQuery } from "@tanstack/react-query";
import { jobsService } from "@/services/jobs.service";
import type { JobFilters } from "@/services/jobs.service";

export function useJobs(filters: JobFilters = {}) {
  return useQuery({
    queryKey: ["opportunities", filters],
    queryFn: () => jobsService.list(filters),
  });
}
