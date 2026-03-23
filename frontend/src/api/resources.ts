import apiClient from "./client";
import type { Resource, PaginatedResponse, Relationship, SubgraphResponse, DriftResponse, DriftExistsResponse, DriftTimelineResponse, FleetDriftTimelineResponse, AssetTwinsResponse, AssetChainResponse } from "./types";

export interface ListResourcesParams {
  vendor?: string;
  category?: string;
  region?: string;
  state?: string;
  cursor?: string;
  page_size?: number;
  search?: string;
}

export async function listResources(params: ListResourcesParams = {}): Promise<PaginatedResponse<Resource>> {
  const res = await apiClient.get<PaginatedResponse<Resource>>("/resources", { params });
  return res.data;
}

export async function getResource(uid: string): Promise<Resource> {
  const res = await apiClient.get<Resource>(`/resources/${uid}`);
  return res.data;
}

export async function getResourceRelationships(
  uid: string,
  params: { direction?: string; type?: string; cursor?: string; page_size?: number } = {}
): Promise<PaginatedResponse<Relationship>> {
  const res = await apiClient.get<PaginatedResponse<Relationship>>(`/resources/${uid}/relationships`, { params });
  return res.data;
}

export async function getResourceGraph(uid: string, depth: number = 1): Promise<SubgraphResponse> {
  const res = await apiClient.get<SubgraphResponse>(`/resources/${uid}/graph`, { params: { depth } });
  return res.data;
}

export async function getResourceDrift(uid: string): Promise<DriftResponse> {
  const res = await apiClient.get<DriftResponse>(`/resources/${uid}/drift`);
  return res.data;
}

export async function getResourceDriftExists(uid: string): Promise<DriftExistsResponse> {
  const res = await apiClient.get<DriftExistsResponse>(`/resources/${uid}/drift/exists`);
  return res.data;
}

export async function getResourceDriftTimeline(
  uid: string,
  start?: string,
  end?: string,
): Promise<DriftTimelineResponse> {
  const params: Record<string, string> = {};
  if (start) params.start = start;
  if (end) params.end = end;
  const res = await apiClient.get<DriftTimelineResponse>(`/resources/${uid}/drift/timeline`, { params });
  return res.data;
}

export async function getAssetTwins(uid: string): Promise<AssetTwinsResponse> {
  const res = await apiClient.get<AssetTwinsResponse>(`/resources/${uid}/asset-twins`);
  return res.data;
}

export async function getAssetChain(uid: string): Promise<AssetChainResponse> {
  const res = await apiClient.get<AssetChainResponse>(`/resources/${uid}/asset-chain`);
  return res.data;
}

export async function scanCorrelations(): Promise<{ created: number; correlations: unknown[] }> {
  const res = await apiClient.post<{ created: number; correlations: unknown[] }>("/correlations/scan");
  return res.data;
}

export async function getFleetDriftTimeline(
  start?: string,
  end?: string,
): Promise<FleetDriftTimelineResponse> {
  const params: Record<string, string> = {};
  if (start) params.start = start;
  if (end) params.end = end;
  const res = await apiClient.get<FleetDriftTimelineResponse>("/drift/fleet-timeline", { params });
  return res.data;
}
