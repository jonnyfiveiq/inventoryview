import { useState, useEffect, useRef, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useInfiniteResources } from "@/hooks/useResources";
import { useTracking } from "@/hooks/useTracking";
import FilterBar from "@/components/provider/FilterBar";
import ResourceTable from "@/components/provider/ResourceTable";
import GraphOverlay from "@/components/graph/GraphOverlay";
import DriftCalendar from "@/components/drift/DriftCalendar";
import ErrorBanner from "@/components/layout/ErrorBanner";
import type { Resource } from "@/api/types";

export default function ProviderPage() {
  const { vendor } = useParams<{ vendor: string }>();
  const { track } = useTracking();
  const [filters, setFilters] = useState<Record<string, string | undefined>>({});
  const [graphUid, setGraphUid] = useState<string | null>(null);

  useEffect(() => { track("Resource Browsing", "page_view"); }, [vendor]);

  const queryParams = {
    vendor,
    ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)),
  };

  const {
    data,
    isLoading,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteResources(queryParams);

  const loadMoreRef = useRef<HTMLDivElement>(null);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    },
    [hasNextPage, isFetchingNextPage, fetchNextPage]
  );

  useEffect(() => {
    const observer = new IntersectionObserver(handleObserver, { threshold: 0.1 });
    if (loadMoreRef.current) observer.observe(loadMoreRef.current);
    return () => observer.disconnect();
  }, [handleObserver]);

  const allResources: Resource[] = data?.pages.flatMap((p) => p.data) ?? [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1 capitalize">{vendor}</h1>
      <p className="text-text-muted text-sm mb-6">
        {allResources.length} resources loaded
        {hasNextPage && " (scroll for more)"}
      </p>

      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-3">Drift Activity</h2>
        <div className="bg-surface border border-border rounded-lg p-4">
          <DriftCalendar mode="fleet" />
        </div>
      </div>

      <div className="mb-4">
        <FilterBar
          filters={filters}
          onFilterChange={setFilters}
          resources={allResources}
        />
      </div>

      {error ? (
        <ErrorBanner message="Failed to load resources." onRetry={() => refetch()} />
      ) : isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-surface rounded animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          <ResourceTable resources={allResources} onGraphClick={setGraphUid} />

          <div ref={loadMoreRef} className="h-10 flex items-center justify-center">
            {isFetchingNextPage && (
              <span className="text-sm text-text-muted">Loading more...</span>
            )}
          </div>
        </>
      )}

      {graphUid && (
        <GraphOverlay uid={graphUid} onClose={() => setGraphUid(null)} />
      )}
    </div>
  );
}
