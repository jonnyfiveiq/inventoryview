import { useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useSearch } from "@/hooks/useSearch";
import SearchInput from "./SearchInput";
import SearchResults, { getFlatResults } from "./SearchResults";

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

  const flatResults = getFlatResults(resources);

  const handleNavigate = useCallback(
    (uid: string) => {
      onClose();
      navigate(`/resources/${uid}`);
    },
    [navigate, onClose]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setHighlightedIndex((prev) =>
          flatResults.length === 0 ? -1 : (prev + 1) % flatResults.length
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setHighlightedIndex((prev) =>
          flatResults.length === 0
            ? -1
            : prev <= 0
              ? flatResults.length - 1
              : prev - 1
        );
      } else if (e.key === "Enter" && highlightedIndex >= 0 && highlightedIndex < flatResults.length) {
        e.preventDefault();
        handleNavigate(flatResults[highlightedIndex].uid);
      } else if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    },
    [flatResults, highlightedIndex, handleNavigate, onClose]
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
      </div>
    </div>,
    document.body
  );
}
