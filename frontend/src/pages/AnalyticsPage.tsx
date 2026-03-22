import { BarChart3 } from "lucide-react";
import { useAllResources } from "@/hooks/useResources";
import HeatmapDetail from "@/components/heatmap/HeatmapDetail";
import ErrorBanner from "@/components/layout/ErrorBanner";

export default function AnalyticsPage() {
  const { data, isLoading, error, refetch } = useAllResources();

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="h-8 w-48 bg-surface rounded animate-pulse" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-40 bg-surface rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return <ErrorBanner message="Failed to load analytics data." onRetry={() => refetch()} />;
  }

  if (!data?.data?.length) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <BarChart3 className="w-16 h-16 text-text-dim mb-4" />
        <h2 className="text-xl font-semibold mb-2">No data available</h2>
        <p className="text-text-muted">Run a collector to generate analytics data.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Analytics</h1>
      <HeatmapDetail resources={data.data} />
    </div>
  );
}
