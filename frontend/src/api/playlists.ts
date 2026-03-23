import apiClient from "./client";
import type {
  Playlist,
  PlaylistDetailResponse,
  PlaylistMembership,
  PlaylistActivity,
  PlaylistActivityTimelineDay,
  PlaylistActivityTimelineResponse,
  PaginatedResponse,
} from "./types";

export async function listPlaylists(): Promise<PaginatedResponse<Playlist>> {
  const res = await apiClient.get<PaginatedResponse<Playlist>>("/playlists", {
    params: { page_size: 200 },
  });
  return res.data;
}

export async function createPlaylist(name: string, description?: string): Promise<Playlist> {
  const res = await apiClient.post<Playlist>("/playlists", { name, description });
  return res.data;
}

export async function getPlaylist(
  identifier: string,
  detail: "summary" | "full" = "summary",
): Promise<PlaylistDetailResponse> {
  const res = await apiClient.get<PlaylistDetailResponse>(`/playlists/${identifier}`, {
    params: { detail },
  });
  return res.data;
}

export async function updatePlaylist(
  identifier: string,
  updates: { name?: string; description?: string },
): Promise<Playlist> {
  const res = await apiClient.patch<Playlist>(`/playlists/${identifier}`, updates);
  return res.data;
}

export async function deletePlaylist(identifier: string): Promise<void> {
  await apiClient.delete(`/playlists/${identifier}`);
}

export async function addResourceToPlaylist(
  identifier: string,
  resourceUid: string,
): Promise<PlaylistMembership> {
  const res = await apiClient.post<PlaylistMembership>(`/playlists/${identifier}/members`, {
    resource_uid: resourceUid,
  });
  return res.data;
}

export async function removeResourceFromPlaylist(
  identifier: string,
  resourceUid: string,
): Promise<void> {
  await apiClient.delete(`/playlists/${identifier}/members/${resourceUid}`);
}

export async function getPlaylistsForResource(
  resourceUid: string,
): Promise<{ data: Playlist[] }> {
  const res = await apiClient.get<{ data: Playlist[] }>(`/resources/${resourceUid}/playlists`);
  return res.data;
}

export async function getPlaylistActivity(
  identifier: string,
  params?: { date?: string; cursor?: string; page_size?: number },
): Promise<PaginatedResponse<PlaylistActivity>> {
  const res = await apiClient.get<PaginatedResponse<PlaylistActivity>>(
    `/playlists/${identifier}/activity`,
    { params },
  );
  return res.data;
}

export async function getPlaylistActivityTimeline(
  identifier: string,
  start?: string,
  end?: string,
): Promise<PlaylistActivityTimelineResponse> {
  const params: Record<string, string> = {};
  if (start) params.start = start;
  if (end) params.end = end;
  const res = await apiClient.get<PlaylistActivityTimelineResponse>(
    `/playlists/${identifier}/activity/timeline`,
    { params },
  );
  return res.data;
}
