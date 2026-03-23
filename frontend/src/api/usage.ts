import apiClient from "./client";

// -- Types --

export interface Period {
  start: string;
  end: string;
}

export interface FeatureAreaSummary {
  feature_area: string;
  total_events: number;
  unique_users: number;
  trend: "up" | "down" | "flat";
  trend_percentage: number;
}

export interface UsageSummaryResponse {
  period: Period;
  feature_areas: FeatureAreaSummary[];
  total_events: number;
  total_unique_users: number;
}

export interface ActionBreakdown {
  action: string;
  count: number;
  unique_users: number;
}

export interface FeatureDetailResponse {
  feature_area: string;
  period: Period;
  actions: ActionBreakdown[];
  total_events: number;
}

export interface LoginAuditEntry {
  id: string;
  username: string;
  outcome: "success" | "failure";
  failure_reason: string | null;
  ip_address: string;
  created_at: string;
}

export interface LoginSummary {
  total_attempts: number;
  successful: number;
  failed: number;
  unique_users: number;
}

export interface LoginAuditResponse {
  period: Period;
  summary: LoginSummary;
  entries: LoginAuditEntry[];
  page: number;
  page_size: number;
  total_count: number;
}

// -- API calls --

export async function trackEvent(featureArea: string, action: string): Promise<void> {
  await apiClient.post("/usage/events", { feature_area: featureArea, action });
}

export async function trackEventsBatch(
  events: { feature_area: string; action: string }[],
): Promise<void> {
  await apiClient.post("/usage/events/batch", { events });
}

export async function getUsageSummary(
  startDate?: string,
  endDate?: string,
): Promise<UsageSummaryResponse> {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const res = await apiClient.get<UsageSummaryResponse>("/usage/summary", { params });
  return res.data;
}

export async function getFeatureDetail(
  featureArea: string,
  startDate?: string,
  endDate?: string,
): Promise<FeatureDetailResponse> {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const res = await apiClient.get<FeatureDetailResponse>(
    `/usage/feature/${encodeURIComponent(featureArea)}`,
    { params },
  );
  return res.data;
}

export async function getLoginAudit(
  startDate?: string,
  endDate?: string,
  page = 1,
  pageSize = 50,
): Promise<LoginAuditResponse> {
  const params: Record<string, string | number> = { page, page_size: pageSize };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const res = await apiClient.get<LoginAuditResponse>("/usage/logins", { params });
  return res.data;
}
