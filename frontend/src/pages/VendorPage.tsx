import { useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Network } from "lucide-react";
import { useAllResources } from "@/hooks/useResources";
import GraphOverlay from "@/components/graph/GraphOverlay";
import ErrorBanner from "@/components/layout/ErrorBanner";
import type { Resource } from "@/api/types";

const vendorColors: Record<string, string> = {
  vmware: "#60a5fa",
  aws: "#f59e0b",
  azure: "#06b6d4",
  openshift: "#ef4444",
};

const stateIndicators: Record<string, string> = {
  poweredon: "bg-state-on",
  running: "bg-state-on",
  connected: "bg-state-connected",
  active: "bg-state-on",
  available: "bg-state-on",
  ready: "bg-state-on",
  online: "bg-state-on",
  admitted: "bg-state-on",
  bound: "bg-state-on",
  poweredoff: "bg-state-off",
  stopped: "bg-state-off",
  deallocated: "bg-state-off",
  not_ready: "bg-state-error",
  maintenance: "bg-state-maintenance",
  error: "bg-state-error",
};

function formatType(ntype: string): string {
  if (!ntype) return "Other";
  return ntype.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function stateClass(state: string | null): string {
  if (!state) return "bg-text-dim";
  return stateIndicators[state.toLowerCase()] || "bg-text-dim";
}

export default function VendorPage() {
  const { vendor } = useParams<{ vendor: string }>();
  const { data, isLoading, error, refetch } = useAllResources();
  const [graphUid, setGraphUid] = useState<string | null>(null);

  const grouped = useMemo(() => {
    if (!data?.data || !vendor) return [];
    const vendorResources = data.data.filter(
      (r) => r.vendor.toLowerCase() === vendor.toLowerCase()
    );
    const groups: Record<string, Resource[]> = {};
    for (const r of vendorResources) {
      const key = r.normalised_type;
      if (!groups[key]) groups[key] = [];
      groups[key].push(r);
    }
    // Sort groups by count descending, resources within each by name
    return Object.entries(groups)
      .sort((a, b) => b[1].length - a[1].length)
      .map(([type, resources]) => [type, resources.sort((a, b) => a.name.localeCompare(b.name))] as [string, Resource[]]);
  }, [data, vendor]);

  const totalCount = grouped.reduce((sum, [, r]) => sum + r.length, 0);
  const color = vendorColors[vendor?.toLowerCase() ?? ""] || "#6366f1";

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-6 w-32 bg-surface rounded animate-pulse" />
        <div className="h-8 w-64 bg-surface rounded animate-pulse" />
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-48 bg-surface rounded-lg animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Link to="/" className="flex items-center gap-1 text-sm text-text-muted hover:text-text">
          <ArrowLeft className="w-4 h-4" /> Back
        </Link>
        <ErrorBanner message="Failed to load resources." onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div>
      <Link to="/" className="flex items-center gap-1 text-sm text-text-muted hover:text-text mb-4">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <div className="flex items-center gap-3 mb-6">
        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
        <h1 className="text-2xl font-bold capitalize" style={{ color }}>
          {vendor}
        </h1>
        <span className="text-text-muted text-sm">
          {totalCount} resources across {grouped.length} types
        </span>
      </div>

      {grouped.length === 0 && (
        <p className="text-text-muted">No resources found for this vendor.</p>
      )}

      <div className="space-y-6">
        {grouped.map(([type, resources]) => (
          <section key={type}>
            <div className="flex items-center gap-2 mb-3">
              <h2 className="text-base font-semibold text-text">{formatType(type)}</h2>
              <span className="text-xs text-text-dim bg-surface-hover rounded-full px-2 py-0.5">
                {resources.length}
              </span>
            </div>
            <div className="bg-surface border border-border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-text-muted">
                    <th className="text-left px-4 py-2.5 font-medium">Name</th>
                    <th className="text-left px-4 py-2.5 font-medium">State</th>
                    <th className="text-left px-4 py-2.5 font-medium">Region</th>
                    <th className="text-left px-4 py-2.5 font-medium">Category</th>
                    <th className="text-left px-4 py-2.5 font-medium w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {resources.map((r) => (
                    <tr key={r.uid} className="border-b border-border/50 hover:bg-surface-hover">
                      <td className="px-4 py-2.5">
                        <Link
                          to={`/resources/${r.uid}`}
                          className="text-accent hover:text-accent-hover font-medium"
                        >
                          {r.name}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5">
                          <span className={`w-2 h-2 rounded-full ${stateClass(r.state)}`} />
                          <span className="text-text-muted">{r.state ?? "unknown"}</span>
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-text-muted">
                        {r.region ?? "—"}
                      </td>
                      <td className="px-4 py-2.5 text-text-muted capitalize">
                        {r.category}
                      </td>
                      <td className="px-4 py-2.5">
                        <button
                          onClick={() => setGraphUid(r.uid)}
                          className="p-1 rounded text-text-dim hover:text-accent transition-colors"
                          title="View graph"
                        >
                          <Network className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ))}
      </div>

      {graphUid && (
        <GraphOverlay uid={graphUid} onClose={() => setGraphUid(null)} />
      )}
    </div>
  );
}
