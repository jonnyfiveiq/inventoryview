import { useMemo } from "react";
import { Search } from "lucide-react";
import type { Resource } from "@/api/types";
import TaxonomyGroup from "./TaxonomyGroup";

interface TaxonomyGroupData {
  type: string;
  items: Resource[];
}

interface SearchResultsProps {
  resources: Resource[] | undefined;
  isLoading: boolean;
  isError: boolean;
  query: string;
  highlightedIndex: number;
  onNavigate: (uid: string) => void;
}

export default function SearchResults({
  resources,
  isLoading,
  isError,
  query,
  highlightedIndex,
  onNavigate,
}: SearchResultsProps) {
  const groups: TaxonomyGroupData[] = useMemo(() => {
    if (!resources || resources.length === 0) return [];
    const map = new Map<string, Resource[]>();
    for (const r of resources) {
      const type = r.normalised_type || "unknown";
      if (!map.has(type)) map.set(type, []);
      map.get(type)!.push(r);
    }
    return Array.from(map.entries())
      .map(([type, items]) => ({ type, items }))
      .sort((a, b) => b.items.length - a.items.length);
  }, [resources]);

  if (query.length < 2) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-text-dim">
        <Search className="w-8 h-8 mb-3 opacity-40" />
        <p className="text-sm">Start typing to search...</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="px-3 py-8 text-center text-sm text-red-400">
        Search failed. Please try again.
      </div>
    );
  }

  if (groups.length === 0) {
    return (
      <div className="px-3 py-8 text-center text-sm text-text-dim">
        No results found for "{query}"
      </div>
    );
  }

  let runningIndex = 0;

  return (
    <div className="py-2 max-h-[60vh] overflow-y-auto">
      {groups.map((group) => {
        const startIndex = runningIndex;
        runningIndex += Math.min(group.items.length, 10);
        return (
          <TaxonomyGroup
            key={group.type}
            type={group.type}
            items={group.items}
            totalCount={group.items.length}
            highlightedIndex={highlightedIndex}
            startIndex={startIndex}
            onNavigate={onNavigate}
          />
        );
      })}
    </div>
  );
}

export function getFlatResults(resources: Resource[] | undefined): Resource[] {
  if (!resources || resources.length === 0) return [];
  const map = new Map<string, Resource[]>();
  for (const r of resources) {
    const type = r.normalised_type || "unknown";
    if (!map.has(type)) map.set(type, []);
    map.get(type)!.push(r);
  }
  const groups = Array.from(map.entries())
    .map(([type, items]) => ({ type, items }))
    .sort((a, b) => b.items.length - a.items.length);

  const flat: Resource[] = [];
  for (const g of groups) {
    flat.push(...g.items.slice(0, 10));
  }
  return flat;
}
