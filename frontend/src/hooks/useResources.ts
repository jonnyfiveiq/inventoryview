import { useQuery, useInfiniteQuery } from "@tanstack/react-query";
import { listResources, getResource, getResourceRelationships, getResourceDrift, getResourceDriftExists, type ListResourcesParams } from "@/api/resources";
import type { Resource, PaginatedResponse, Relationship } from "@/api/types";

export function useResourceList(params: ListResourcesParams = {}, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["resources", params],
    queryFn: () => listResources(params),
    enabled: options?.enabled,
  });
}

export function useAllResources(pageSize: number = 200) {
  return useQuery({
    queryKey: ["resources", "all", pageSize],
    queryFn: () => listResources({ page_size: pageSize }),
  });
}

export function useResource(uid: string) {
  return useQuery({
    queryKey: ["resource", uid],
    queryFn: () => getResource(uid),
    enabled: !!uid,
  });
}

export function useResourceRelationships(uid: string, params?: { direction?: string; type?: string }) {
  return useQuery({
    queryKey: ["resource", uid, "relationships", params],
    queryFn: () => getResourceRelationships(uid, params),
    enabled: !!uid,
  });
}

export function useResourceDriftExists(uid: string) {
  return useQuery({
    queryKey: ["resource", uid, "drift-exists"],
    queryFn: () => getResourceDriftExists(uid),
    enabled: !!uid,
    staleTime: 60 * 1000,
  });
}

export function useResourceDrift(uid: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["resource", uid, "drift"],
    queryFn: () => getResourceDrift(uid),
    enabled: !!uid && enabled,
  });
}

export function useInfiniteResources(params: Omit<ListResourcesParams, "cursor"> = {}) {
  return useInfiniteQuery<PaginatedResponse<Resource>>({
    queryKey: ["resources", "infinite", params],
    queryFn: ({ pageParam }) =>
      listResources({ ...params, cursor: pageParam as string | undefined }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  });
}
