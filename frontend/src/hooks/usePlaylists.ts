import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listPlaylists,
  createPlaylist,
  getPlaylist,
  updatePlaylist,
  deletePlaylist,
  addResourceToPlaylist,
  removeResourceFromPlaylist,
  getPlaylistsForResource,
  getPlaylistActivity,
  getPlaylistActivityTimeline,
} from "@/api/playlists";

export function usePlaylists() {
  return useQuery({
    queryKey: ["playlists"],
    queryFn: listPlaylists,
    staleTime: 30 * 1000,
  });
}

export function usePlaylist(identifier: string, detail: "summary" | "full" = "summary") {
  return useQuery({
    queryKey: ["playlist", identifier, detail],
    queryFn: () => getPlaylist(identifier, detail),
    enabled: !!identifier,
  });
}

export function usePlaylistsForResource(resourceUid: string) {
  return useQuery({
    queryKey: ["resource", resourceUid, "playlists"],
    queryFn: () => getPlaylistsForResource(resourceUid),
    enabled: !!resourceUid,
    staleTime: 30 * 1000,
  });
}

export function usePlaylistActivity(
  identifier: string,
  params?: { date?: string; cursor?: string; page_size?: number },
) {
  return useQuery({
    queryKey: ["playlist", identifier, "activity", params],
    queryFn: () => getPlaylistActivity(identifier, params),
    enabled: !!identifier,
  });
}

export function usePlaylistActivityTimeline(
  identifier: string,
  start?: string,
  end?: string,
) {
  return useQuery({
    queryKey: ["playlist", identifier, "activity-timeline", start, end],
    queryFn: () => getPlaylistActivityTimeline(identifier, start, end),
    enabled: !!identifier,
    staleTime: 60 * 1000,
  });
}

export function useCreatePlaylist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ name, description }: { name: string; description?: string }) =>
      createPlaylist(name, description),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["playlists"] });
    },
  });
}

export function useUpdatePlaylist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      identifier,
      updates,
    }: {
      identifier: string;
      updates: { name?: string; description?: string };
    }) => updatePlaylist(identifier, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["playlists"] });
      queryClient.invalidateQueries({ queryKey: ["playlist"] });
    },
  });
}

export function useDeletePlaylist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (identifier: string) => deletePlaylist(identifier),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["playlists"] });
    },
  });
}

export function useAddToPlaylist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      identifier,
      resourceUid,
    }: {
      identifier: string;
      resourceUid: string;
    }) => addResourceToPlaylist(identifier, resourceUid),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["playlists"] });
      queryClient.invalidateQueries({ queryKey: ["playlist"] });
      queryClient.invalidateQueries({
        queryKey: ["resource", variables.resourceUid, "playlists"],
      });
    },
  });
}

export function useRemoveFromPlaylist() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      identifier,
      resourceUid,
    }: {
      identifier: string;
      resourceUid: string;
    }) => removeResourceFromPlaylist(identifier, resourceUid),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["playlists"] });
      queryClient.invalidateQueries({ queryKey: ["playlist"] });
      queryClient.invalidateQueries({
        queryKey: ["resource", variables.resourceUid, "playlists"],
      });
    },
  });
}
