"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { proposalService } from "@/services/proposal.service";
import type { ProposalEditRequest, ImproveRequest } from "@/types/proposal";

export function useProposals() {
  const queryClient = useQueryClient();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["proposals"] });

  const list = (params?: { skip?: number; limit?: number; status?: string }) =>
    useQuery({
      queryKey: ["proposals", params],
      queryFn: () => proposalService.list(params),
    });

  const getById = (id: string) =>
    useQuery({
      queryKey: ["proposals", id],
      queryFn: () => proposalService.getById(id),
      enabled: !!id,
    });

  const create = useMutation({
    mutationFn: (data: { project_id: string; cover_letter?: string; bid_amount?: number }) =>
      proposalService.create(data),
    onSuccess: invalidate,
  });

  const review = useMutation({
    mutationFn: (id: string) => proposalService.review(id),
    onSuccess: invalidate,
  });

  const markReady = useMutation({
    mutationFn: (id: string) => proposalService.markReady(id),
    onSuccess: invalidate,
  });

  const markSubmitted = useMutation({
    mutationFn: (id: string) => proposalService.markSubmitted(id),
    onSuccess: invalidate,
  });

  const archive = useMutation({
    mutationFn: (id: string) => proposalService.archive(id),
    onSuccess: invalidate,
  });

  const readiness = (id: string) =>
    useQuery({
      queryKey: ["proposals", id, "readiness"],
      queryFn: () => proposalService.readiness(id),
      enabled: !!id,
    });

  const edit = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProposalEditRequest }) =>
      proposalService.edit(id, data),
    onSuccess: invalidate,
  });

  const versions = (id: string) =>
    useQuery({
      queryKey: ["proposals", id, "versions"],
      queryFn: () => proposalService.versions(id),
      enabled: !!id,
    });

  const notes = (id: string) =>
    useQuery({
      queryKey: ["proposals", id, "notes"],
      queryFn: () => proposalService.notes(id),
      enabled: !!id,
    });

  const improve = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ImproveRequest }) =>
      proposalService.improve(id, data),
    onSuccess: invalidate,
  });

  const evaluate = useMutation({
    mutationFn: (id: string) => proposalService.evaluate(id),
  });

  const requestApproval = useMutation({
    mutationFn: (id: string) => proposalService.requestApproval(id),
    onSuccess: invalidate,
  });

  const approve = useMutation({
    mutationFn: (id: string) => proposalService.approve(id),
    onSuccess: invalidate,
  });

  const reject = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      proposalService.reject(id, reason),
    onSuccess: invalidate,
  });

  const queue = useMutation({
    mutationFn: (id: string) => proposalService.queue(id),
    onSuccess: invalidate,
  });

  return {
    list, getById, create,
    review, markReady, markSubmitted, archive,
    readiness, edit, versions, notes,
    improve, evaluate,
    requestApproval, approve, reject, queue,
    auditLog: getById,
  };
}
