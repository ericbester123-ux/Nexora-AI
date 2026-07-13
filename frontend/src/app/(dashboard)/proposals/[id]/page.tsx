"use client";

import { use } from "react";
import { useProposals } from "@/hooks/useProposals";
import { ProposalReview } from "@/components/proposals/ProposalReview";
import { PageLoader } from "@/components/shared/LoadingSpinner";
import { ErrorState } from "@/components/shared/ErrorState";

export default function ProposalPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { getById } = useProposals();
  const { data: proposal, isLoading, error, refetch } = getById(id);

  if (isLoading) return <PageLoader />;
  if (error || !proposal) return <ErrorState message="Proposal not found" onRetry={refetch} />;

  return <ProposalReview proposal={proposal} id={id} />;
}
