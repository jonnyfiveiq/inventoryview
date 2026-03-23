import { Link } from "react-router-dom";
import { Activity } from "lucide-react";
import { useCoverageStats } from "@/hooks/useAutomation";

export default function AutomationCoverage() {
  const { data, isLoading } = useCoverageStats();

  if (isLoading) {
    return <div className="h-24 bg-surface rounded-lg animate-pulse" />;
  }

  if (!data || data.total_resources === 0) {
    return null;
  }

  return (
    <Link
      to="/automations"
      className="block bg-surface border border-accent/20 rounded-lg p-4 hover:bg-surface-hover transition-colors group"
    >
      <div className="flex items-center gap-2 mb-2">
        <Activity className="w-4 h-4 text-accent" />
        <span className="text-sm font-semibold text-accent group-hover:underline">
          Automation Coverage
        </span>
      </div>
      <div className="flex items-center gap-4">
        <div>
          <span className="text-2xl font-bold text-text">{data.coverage_percentage}%</span>
          <span className="text-xs text-text-muted ml-1">covered</span>
        </div>
        <div className="flex-1 h-2 bg-background rounded overflow-hidden">
          <div
            className="h-full bg-accent/60 rounded transition-all"
            style={{ width: `${Math.max(data.coverage_percentage, 2)}%` }}
          />
        </div>
        <div className="text-xs text-text-muted">
          {data.automated_resources} / {data.total_resources}
        </div>
      </div>
    </Link>
  );
}
