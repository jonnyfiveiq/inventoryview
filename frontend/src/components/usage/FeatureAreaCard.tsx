import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FeatureAreaSummary } from "@/api/usage";

interface FeatureAreaCardProps {
  data: FeatureAreaSummary;
  onClick?: () => void;
}

export default function FeatureAreaCard({ data, onClick }: FeatureAreaCardProps) {
  const TrendIcon =
    data.trend === "up" ? TrendingUp : data.trend === "down" ? TrendingDown : Minus;

  const trendColor =
    data.trend === "up"
      ? "text-emerald-400"
      : data.trend === "down"
        ? "text-red-400"
        : "text-text-dim";

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-surface border border-border rounded-lg p-4 hover:bg-surface-hover transition-colors"
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-sm font-medium text-text truncate pr-2">
          {data.feature_area}
        </h3>
        <div className={cn("flex items-center gap-1 text-xs shrink-0", trendColor)}>
          <TrendIcon className="w-3.5 h-3.5" />
          <span>{Math.abs(data.trend_percentage).toFixed(1)}%</span>
        </div>
      </div>

      <div className="flex items-end justify-between">
        <div>
          <div className="text-2xl font-bold text-text">
            {data.total_events.toLocaleString()}
          </div>
          <div className="text-xs text-text-muted mt-0.5">events</div>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold text-text-muted">
            {data.unique_users}
          </div>
          <div className="text-xs text-text-dim mt-0.5">
            {data.unique_users === 1 ? "user" : "users"}
          </div>
        </div>
      </div>
    </button>
  );
}
