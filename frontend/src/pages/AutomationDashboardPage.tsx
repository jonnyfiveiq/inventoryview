import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useCoverageStats } from "@/hooks/useAutomation";
import { useTracking } from "@/hooks/useTracking";
import { Upload, Download } from "lucide-react";

export default function AutomationDashboardPage() {
  const { track } = useTracking();
  const { data, isLoading } = useCoverageStats();

  useEffect(() => { track("Automation Metrics", "page_view"); }, []);

  const handleExportCSV = () => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || "/api/v1";
    window.open(`${baseUrl}/automations/reports/coverage?format=csv`, "_blank");
  };

  if (isLoading) {
    return <div className="text-text-muted">Loading coverage data...</div>;
  }

  if (!data || data.total_resources === 0) {
    return (
      <div className="text-center py-16">
        <Upload className="w-12 h-12 text-text-dim mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-text mb-2">No Automation Data</h2>
        <p className="text-sm text-text-muted mb-4">Upload AAP metrics utility data to see coverage.</p>
        <Link
          to="/automations/upload"
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent text-background rounded-lg hover:bg-accent/80 transition-colors"
        >
          <Upload className="w-4 h-4" />
          Upload Metrics Data
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-text">Automation Coverage</h1>
        <button
          onClick={handleExportCSV}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium bg-surface border border-border rounded hover:bg-surface-hover transition-colors text-text-muted"
        >
          <Download className="w-3.5 h-3.5" />
          Export CSV
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-surface border border-border rounded-lg p-5">
          <div className="text-[10px] text-text-dim uppercase tracking-wider">Total Resources</div>
          <div className="text-3xl font-bold text-text mt-1">{data.total_resources.toLocaleString()}</div>
        </div>
        <div className="bg-surface border border-accent/30 rounded-lg p-5">
          <div className="text-[10px] text-text-dim uppercase tracking-wider">Automated</div>
          <div className="text-3xl font-bold text-accent mt-1">{data.automated_resources.toLocaleString()}</div>
        </div>
        <div className="bg-surface border border-border rounded-lg p-5">
          <div className="text-[10px] text-text-dim uppercase tracking-wider">Coverage</div>
          <div className="text-3xl font-bold text-text mt-1">{data.coverage_percentage}%</div>
        </div>
      </div>

      {/* By provider */}
      {data.by_provider.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-5 mb-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-4">
            Coverage by Provider
          </h2>
          <div className="space-y-3">
            {data.by_provider.map((p) => (
              <div key={p.vendor} className="flex items-center gap-3">
                <span className="text-sm text-text w-20 capitalize truncate">{p.vendor}</span>
                <div className="flex-1 h-5 bg-background rounded overflow-hidden">
                  <div
                    className="h-full bg-accent/60 rounded transition-all"
                    style={{ width: `${Math.max(p.coverage_percentage, 2)}%` }}
                  />
                </div>
                <span className="text-xs text-text-muted w-28 text-right">
                  {p.automated} / {p.total} ({p.coverage_percentage}%)
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top automated */}
      {data.top_automated.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-5 mb-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-4">
            Top Automated Resources
          </h2>
          <div className="space-y-2">
            {data.top_automated.map((r) => (
              <Link
                key={r.resource_uid}
                to={`/resources/${r.resource_uid}`}
                className="flex items-center justify-between p-2 rounded hover:bg-surface-hover transition-colors"
              >
                <div>
                  <span className="text-sm text-text">{r.resource_name}</span>
                  <span className="text-xs text-text-dim ml-2 capitalize">{r.vendor}</span>
                </div>
                <span className="text-xs font-medium text-accent">{r.total_jobs} jobs</span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Recent imports */}
      {data.recent_imports.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-4">
            Recent Imports
          </h2>
          <div className="space-y-2">
            {data.recent_imports.map((imp, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <span className="text-text">{imp.source_label}</span>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-text-muted">{imp.hosts_count} hosts</span>
                  <span className="text-xs text-text-dim">
                    {new Date(imp.imported_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
