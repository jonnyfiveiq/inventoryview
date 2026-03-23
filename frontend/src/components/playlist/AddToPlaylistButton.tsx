import { useState, useRef, useEffect } from "react";
import { ListMusic, Check } from "lucide-react";
import {
  usePlaylists,
  usePlaylistsForResource,
  useAddToPlaylist,
  useRemoveFromPlaylist,
} from "@/hooks/usePlaylists";

interface AddToPlaylistButtonProps {
  resourceUid: string;
}

export default function AddToPlaylistButton({ resourceUid }: AddToPlaylistButtonProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { data: allPlaylists } = usePlaylists();
  const { data: resourcePlaylists } = usePlaylistsForResource(resourceUid);
  const addMutation = useAddToPlaylist();
  const removeMutation = useRemoveFromPlaylist();

  const playlists = allPlaylists?.data ?? [];
  const memberOf = new Set((resourcePlaylists?.data ?? []).map((p) => p.id));

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const toggle = (playlistId: string, slug: string, isMember: boolean) => {
    if (isMember) {
      removeMutation.mutate({ identifier: slug, resourceUid });
    } else {
      addMutation.mutate({ identifier: slug, resourceUid });
    }
  };

  if (playlists.length === 0) return null;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-4 py-2 bg-surface border border-border hover:bg-surface-hover text-text rounded-md transition-colors text-sm"
      >
        <ListMusic className="w-4 h-4 text-accent" />
        Add to Playlist
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-64 bg-surface border border-border rounded-lg shadow-lg z-50 py-1 max-h-64 overflow-y-auto">
          {playlists.map((pl) => {
            const isMember = memberOf.has(pl.id);
            return (
              <button
                key={pl.id}
                onClick={() => toggle(pl.id, pl.slug, isMember)}
                className="flex items-center w-full px-3 py-2 text-sm text-left hover:bg-surface-hover transition-colors"
              >
                <span
                  className={`w-4 h-4 rounded border mr-2 flex items-center justify-center shrink-0 ${
                    isMember
                      ? "bg-accent border-accent"
                      : "border-border"
                  }`}
                >
                  {isMember && <Check className="w-3 h-3 text-white" />}
                </span>
                <span className="truncate flex-1">{pl.name}</span>
                <span className="text-[10px] text-text-dim ml-1">{pl.member_count}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
