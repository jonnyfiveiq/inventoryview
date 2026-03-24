import apiClient from "./client";
import type {
  UploadResponse,
  AAPHostListResponse,
  PendingMatchListResponse,
  ReviewAction,
  ReviewResponse,
  CoverageResponse,
  HistoryResponse,
  AutomationGraphResponse,
  CorrelationJobResponse,
  ResourceCorrelationResponse,
  FleetTemperatureResponse,
} from "./types";

export async function uploadMetrics(
  file: File,
  sourceLabel?: string,
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (sourceLabel) {
    formData.append("source_label", sourceLabel);
  }
  const res = await apiClient.post<UploadResponse>("/automations/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120_000,
  });
  return res.data;
}

export async function listHosts(params?: {
  cursor?: string;
  limit?: number;
  status?: string;
  search?: string;
}): Promise<AAPHostListResponse> {
  const res = await apiClient.get<AAPHostListResponse>("/automations/hosts", { params });
  return res.data;
}

export async function listPending(params?: {
  cursor?: string;
  limit?: number;
  min_score?: number;
  max_score?: number;
  sort?: string;
}): Promise<PendingMatchListResponse> {
  const res = await apiClient.get<PendingMatchListResponse>("/automations/pending", { params });
  return res.data;
}

export async function reviewPending(
  actions: ReviewAction[],
): Promise<ReviewResponse> {
  const res = await apiClient.post<ReviewResponse>("/automations/pending/review", { actions });
  return res.data;
}

export async function getCoverage(): Promise<CoverageResponse> {
  const res = await apiClient.get<CoverageResponse>("/automations/coverage");
  return res.data;
}

export async function getResourceHistory(
  resourceUid: string,
  params?: { cursor?: string; limit?: number },
): Promise<HistoryResponse> {
  const res = await apiClient.get<HistoryResponse>(
    `/automations/resources/${resourceUid}/history`,
    { params },
  );
  return res.data;
}

export async function getCoverageReport(params?: {
  format?: string;
  vendor?: string;
}): Promise<unknown> {
  const res = await apiClient.get("/automations/reports/coverage", { params });
  return res.data;
}

export async function getAutomationGraph(
  resourceUid: string,
): Promise<AutomationGraphResponse> {
  const res = await apiClient.get<AutomationGraphResponse>(
    `/automations/graph/${resourceUid}`,
  );
  return res.data;
}

export async function getCorrelationJob(
  jobId: string,
): Promise<CorrelationJobResponse> {
  const res = await apiClient.get<CorrelationJobResponse>(
    `/automations/correlation-jobs/${jobId}`,
  );
  return res.data;
}

export async function getResourceCorrelation(
  uid: string,
): Promise<ResourceCorrelationResponse> {
  const res = await apiClient.get<ResourceCorrelationResponse>(
    `/resources/${uid}/correlation`,
  );
  return res.data;
}

export async function getFleetTemperature(): Promise<FleetTemperatureResponse> {
  const res = await apiClient.get<FleetTemperatureResponse>(
    "/automations/fleet-temperature",
  );
  return res.data;
}

export async function reCorrelate(
  resourceUid: string,
): Promise<{ correlation_job_id: string; message: string }> {
  const res = await apiClient.post("/automations/re-correlate", {
    resource_uid: resourceUid,
  });
  return res.data;
}
