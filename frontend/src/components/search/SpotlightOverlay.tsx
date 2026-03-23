import { useState, useCallback, useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { ListMusic } from "lucide-react";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useSearch } from "@/hooks/useSearch";
import { usePlaylists } from "@/hooks/usePlaylists";
import SearchInput from "./SearchInput";
import SearchResults, { getFlatResults } from "./SearchResults";
import type { Playlist } from "@/api/types";

interface SpotlightOverlayProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SpotlightOverlay({ isOpen, onClose }: SpotlightOverlayProps) {
  const [query, setQuery] = useState("");
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const debouncedQuery = useDebouncedValue(query, 300);
  const navigate = useNavigate();

  const { data, isLoading, isError } = useSearch(debouncedQuery);
  const resources = data?.data;
  const { data: playlistData } = usePlaylists();

  const matchingPlaylists = useMemo(() => {
    if (!playlistData?.data || debouncedQuery.length < 2) return [];
    const q = debouncedQuery.toLowerCase();
    return playlistData.data.filter(
      (pl: Playlist) => pl.name.toLowerCase().includes(q) || pl.slug.toLowerCase().includes(q)
    );
  }, [playlistData, debouncedQuery]);

  const flatResults = getFlatResults(resources);
  const totalNavigable = flatResults.length + matchingPlaylists.length;

  const handleNavigate = useCallback(
    (uid: string) => {
      onClose();
      navigate(`/resources/${uid}`);
    },
    [navigate, onClose]
  );

  const handlePlaylistNavigate = useCallback(
    (slug: string) => {
      onClose();
      navigate(`/playlists/${slug}`);
    },
    [navigate, onClose]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setHighlightedIndex((prev) =>
          totalNavigable === 0 ? -1 : (prev + 1) % totalNavigable
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setHighlightedIndex((prev) =>
          totalNavigable === 0
            ? -1
            : prev <= 0
              ? totalNavigable - 1
              : prev - 1
        );
      } else if (e.key === "Enter" && highlightedIndex >= 0 && highlightedIndex < totalNavigable) {
        e.preventDefault();
        if (highlightedIndex < flatResults.length) {
          handleNavigate(flatResults[highlightedIndex].uid);
        } else {
          const plIdx = highlightedIndex - flatResults.length;
          handlePlaylistNavigate(matchingPlaylists[plIdx].slug);
        }
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    },
    [totalNavigable, flatResults, matchingPlaylists, highlightedIndex, handleNavigate, handlePlaylistNavigate, onClose]
  );

  // Reset state when overlay opens/closes
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setHighlightedIndex(-1);
    }
  }, [isOpen]);

  // Reset highlight when results change
  useEffect(() => {
    setHighlightedIndex(-1);
  }, [debouncedQuery]);

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      {/* Modal */}
      <div className="relative w-full max-w-[600px] mx-4 bg-surface border border-border rounded-xl shadow-2xl overflow-hidden">
        <SearchInput
          value={query}
          onChange={setQuery}
          onKeyDown={handleKeyDown}
        />
        <SearchResults
          resources={resources}
          isLoading={isLoading}
          isError={isError}
          query={debouncedQuery}
          highlightedIndex={highlightedIndex}
          onNavigate={handleNavigate}
        />
        {/* Playlist results */}
        {matchingPlaylists.length > 0 && (
          <div className="border-t border-border py-2">
            <div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-text-dim">
              Playlists
            </div>
            {matchingPlaylists.map((pl: Playlist, i: number) => {
              const idx = flatResults.length + i;
              return (
                <button
                  key={pl.id}
                  onClick={() => handlePlaylistNavigate(pl.slug)}
                  className={`flex items-center gap-3 w-full px-3 py-2 text-sm text-left transition-colors ${
                    idx === highlightedIndex
                      ? "bg-accent/15 text-accent"
                      : "text-text hover:bg-surface-hover"
                  }`}
                >
                  <ListMusic className="w-4 h-4 text-text-dim shrink-0" />
                  <span className="flex-1 truncate">{pl.name}</span>
                  <span className="text-[10px] text-text-dim">{pl.member_count} items</span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}
