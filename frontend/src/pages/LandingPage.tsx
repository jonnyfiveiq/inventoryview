import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Boxes, ListMusic } from "lucide-react";
import { useAllResources } from "@/hooks/useResources";
import { usePlaylists } from "@/hooks/usePlaylists";
import ResourceCarousel from "@/components/carousel/ResourceCarousel";
import VendorCarousel from "@/components/carousel/VendorCarousel";
import HeatmapStrip from "@/components/heatmap/HeatmapStrip";
import DriftCalendar from "@/components/drift/DriftCalendar";
import ErrorBanner from "@/components/layout/ErrorBanner";
import type { Resource } from "@/api/types";

export default function LandingPage() {
  const { data, isLoading, error, refetch } = useAllResources();
  const { data: playlistData } = usePlaylists();
  const playlists = playlistData?.data ?? [];

  const groupedByType = useMemo(() => {
    if (!data?.data) return [];
    const groups: Record<string, Resource[]> = {};
    for (const resource of data.data) {
      const key = resource.normalised_type;
      if (!groups[key]) groups[key] = [];
      groups[key].push(resource);
    }
    // Sort by count descending
    return Object.entries(groups).sort((a, b) => b[1].length - a[1].length);
  }, [data]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Heatmap skeleton */}
        <div className="h-20 bg-surface rounded-lg animate-pulse" />
        {/* Carousel skeletons */}
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-3">
            <div className="h-5 w-40 bg-surface rounded animate-pulse" />
            <div className="flex gap-3">
              {[1, 2, 3, 4].map((j) => (
                <div key={j} className="w-64 h-28 bg-surface rounded-lg animate-pulse shrink-0" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <ErrorBanner
        message="Failed to load resources. Is the backend running?"
        onRetry={() => refetch()}
      />
    );
  }

  if (!data?.data?.length) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <Boxes className="w-16 h-16 text-text-dim mb-4" />
        <h2 className="text-xl font-semibold mb-2">No resources yet</h2>
        <p className="text-text-muted max-w-md">
          Run a collector to discover your infrastructure resources. They'll appear here grouped by type.
        </p>
      </div>
    );
  }

  return (
    <div>
      <HeatmapStrip resources={data.data} />
      <div className="mt-6">
        <h2 className="text-lg font-semibold mb-3">Drift Activity</h2>
        <div className="bg-surface border border-border rounded-lg p-4">
          <DriftCalendar mode="fleet" />
        </div>
      </div>
      <div className="mt-6">
        <VendorCarousel resources={data.data} />
      </div>
      {playlists.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3">
            Playlists
          </h2>
          <div className="flex gap-3 overflow-x-auto pb-2" style={{ scrollbarWidth: "none" }}>
            {playlists.map((pl) => (
              <Link
                key={pl.id}
                to={`/playlists/${pl.slug}`}
                className="flex-shrink-0 w-48 bg-surface border border-accent/20 rounded-lg p-4 hover:bg-surface-hover transition-colors group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <ListMusic className="w-4 h-4 text-accent" />
                  <span className="text-sm font-semibold text-accent group-hover:underline truncate">
                    {pl.name}
                  </span>
                </div>
                <div className="text-xs text-text-muted">
                  <span className="text-text font-medium">{pl.member_count}</span> resource{pl.member_count !== 1 ? "s" : ""}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
      <div className="mt-2">
        {groupedByType.map(([type, resources]) => (
          <ResourceCarousel key={type} type={type} resources={resources} />
        ))}
      </div>
    </div>
  );
}
