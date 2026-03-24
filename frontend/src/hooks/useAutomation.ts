import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  uploadMetrics,
  listHosts,
  listPending,
  reviewPending,
  getCoverage,
  getResourceHistory,
  getCoverageReport,
  getAutomationGraph,
  getCorrelationJob,
  getResourceCorrelation,
  getFleetTemperature,
  reCorrelate,
} from "@/api/automations";
import type { ReviewAction } from "@/api/types";

export function useUploadMetrics() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, sourceLabel }: { file: File; sourceLabel?: string }) =>
      uploadMetrics(file, sourceLabel),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["automation"] });
    },
  });
}

export function useAAPHosts(params?: {
  cursor?: string;
  limit?: number;
  status?: string;
  search?: string;
}) {
  return useQuery({
    queryKey: ["automation", "hosts", params],
    queryFn: () => listHosts(params),
  });
}

export function usePendingMatches(params?: {
  cursor?: string;
  limit?: number;
  min_score?: number;
  max_score?: number;
  tier?: string;
  ambiguity_group?: string;
  sort?: string;
}) {
  return useQuery({
    queryKey: ["automation", "pending", params],
    queryFn: () => listPending(params),
  });
}

export function useReviewMatches() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (actions: ReviewAction[]) => reviewPending(actions),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["automation", "pending"] });
      queryClient.invalidateQueries({ queryKey: ["automation", "hosts"] });
      queryClient.invalidateQueries({ queryKey: ["automation", "coverage"] });
    },
  });
}

export function useCoverageStats() {
  return useQuery({
    queryKey: ["automation", "coverage"],
    queryFn: getCoverage,
    staleTime: 30_000,
  });
}

export function useAutomationHistory(
  resourceUid: string,
  params?: { cursor?: string; limit?: number },
) {
  return useQuery({
    queryKey: ["automation", "history", resourceUid, params],
    queryFn: () => getResourceHistory(resourceUid, params),
    enabled: !!resourceUid,
  });
}

export function useAutomationReport(params?: {
  format?: string;
  vendor?: string;
}) {
  return useQuery({
    queryKey: ["automation", "report", params],
    queryFn: () => getCoverageReport(params),
    enabled: false, // manual trigger
  });
}

export function useAutomationGraph(resourceUid: string) {
  return useQuery({
    queryKey: ["automation", "graph", resourceUid],
    queryFn: () => getAutomationGraph(resourceUid),
    enabled: !!resourceUid,
  });
}

export function useCorrelationJob(
  jobId: string | null,
  { onComplete }: { onComplete?: () => void } = {},
) {
  return useQuery({
    queryKey: ["automation", "correlation-job", jobId],
    queryFn: () => getCorrelationJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") {
        if (status === "completed" && onComplete) {
          onComplete();
        }
        return false;
      }
      return 2_000;
    },
  });
}

export function useResourceCorrelation(uid: string) {
  return useQuery({
    queryKey: ["automation", "correlation", uid],
    queryFn: () => getResourceCorrelation(uid),
    enabled: !!uid,
  });
}

export function useFleetTemperature() {
  return useQuery({
    queryKey: ["automation", "fleet-temperature"],
    queryFn: getFleetTemperature,
    staleTime: 30_000,
  });
}

export function useReCorrelate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (resourceUid: string) => reCorrelate(resourceUid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["automation"] });
    },
  });
}
