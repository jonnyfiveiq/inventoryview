import apiClient from "./client";
import type { Resource, PaginatedResponse, Relationship, SubgraphResponse, DriftResponse, DriftExistsResponse } from "./types";

export interface ListResourcesParams {
  vendor?: string;
  category?: string;
  region?: string;
  state?: string;
  cursor?: string;
  page_size?: number;
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
