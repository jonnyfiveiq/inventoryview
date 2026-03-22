import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { getTaxonomyLabel } from "@/utils/taxonomyLabels";
import type { Resource } from "@/api/types";
import SearchResultItem from "./SearchResultItem";

interface TaxonomyGroupProps {
  type: string;
  items: Resource[];
  totalCount: number;
  highlightedIndex?: number;
  startIndex: number;
  onNavigate: (uid: string) => void;
}

export default function TaxonomyGroup({
  type,
  items,
  totalCount,
  highlightedIndex,
  startIndex,
  onNavigate,
}: TaxonomyGroupProps) {
  const [expanded, setExpanded] = useState(false);
  const navigate = useNavigate();

  const initialLimit = 5;
  const expandedLimit = 10;
  const displayLimit = expanded ? expandedLimit : initialLimit;
  const visibleItems = items.slice(0, displayLimit);
  const hasMore = items.length > displayLimit;
  const hasOverflow = totalCount > expandedLimit;

  return (
    <div className="mb-3">
      <div className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-text-dim uppercase tracking-wider">
        <span>{getTaxonomyLabel(type)}</span>
        <span className="text-text-dim/60">({totalCount})</span>
      </div>
      <div className="space-y-0.5">
        {visibleItems.map((resource, i) => (
          <SearchResultItem
            key={resource.uid}
            resource={resource}
            isHighlighted={highlightedIndex === startIndex + i}
            onClick={() => onNavigate(resource.uid)}
          />
        ))}
      </div>
      {!expanded && hasMore && (
        <button
          onClick={() => setExpanded(true)}
          className="w-full px-3 py-1.5 text-xs text-accent hover:text-accent/80 transition-colors text-left"
        >
          Show more ({Math.min(items.length, expandedLimit) - initialLimit} more)
        </button>
      )}
      {expanded && hasOverflow && (
        <button
          onClick={() => navigate(`/providers/${items[0]?.vendor}?search=${encodeURIComponent(type)}`)}
          className="w-full px-3 py-1.5 text-xs text-accent hover:text-accent/80 transition-colors text-left"
        >
          View all {totalCount} on provider page
        </button>
      )}
    </div>
  );
}
