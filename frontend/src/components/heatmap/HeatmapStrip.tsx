import { useMemo } from "react";
import { Link } from "react-router-dom";
import type { Resource } from "@/api/types";

interface HeatmapStripProps {
  resources: Resource[];
}

const categoryColors: Record<string, string> = {
  compute: "#60a5fa",
  storage: "#f59e0b",
  network: "#22c55e",
  management: "#a855f7",
};

function formatType(ntype: string): string {
  if (!ntype) return "unknown";
  return ntype.replace(/_/g, " ");
}

export default function HeatmapStrip({ resources }: HeatmapStripProps) {
  const { byType, byVendor, recentCount } = useMemo(() => {
    const typeCounts: Record<string, { count: number; category: string }> = {};
    const vendorCounts: Record<string, number> = {};
    let recent = 0;
    const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;

    for (const r of resources) {
      if (!typeCounts[r.normalised_type]) {
        typeCounts[r.normalised_type] = { count: 0, category: r.category };
      }
      typeCounts[r.normalised_type].count++;
      vendorCounts[r.vendor] = (vendorCounts[r.vendor] || 0) + 1;
      if (r.first_seen && new Date(r.first_seen).getTime() > oneDayAgo) {
        recent++;
      }
    }

    return {
      byType: Object.entries(typeCounts)
        .map(([type, { count, category }]) => ({ type, count, category }))
        .sort((a, b) => b.count - a.count),
      byVendor: Object.entries(vendorCounts).sort((a, b) => b[1] - a[1]),
      recentCount: recent,
    };
  }, [resources]);

  const maxTypeCount = Math.max(...byType.map((t) => t.count), 1);

  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-muted">
          Resources Discovered
        </h2>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-text">{resources.length}</span>
          <span className="text-xs text-text-dim">total</span>
          {recentCount > 0 && (
            <span className="text-xs text-state-on ml-2">
              +{recentCount} last 24h
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-6">
        {/* Resource type heatmap grid */}
        <div>
          <div className="text-[10px] text-text-dim uppercase tracking-wider mb-2">
            By Type
          </div>
          <div className="flex flex-wrap gap-1.5">
            {byType.map(({ type, count, category }) => {
              const intensity = count / maxTypeCount;
              const baseColor = categoryColors[category] || "#6b7280";
              return (
                <div
                  key={type}
                  className="relative group cursor-pointer"
                  onClick={() => {
                    const el = document.getElementById(`type-${type}`);
                    if (el) {
                      el.scrollIntoView({ behavior: "smooth", block: "start" });
                    }
                  }}
                >
                  <div
                    className="h-10 rounded flex items-center justify-center gap-1.5 px-3 min-w-[80px] border hover:brightness-125 transition-all"
                    style={{
                      backgroundColor: baseColor + opacityHex(0.15 + intensity * 0.45),
                      borderColor: baseColor + opacityHex(0.3 + intensity * 0.4),
                    }}
                  >
                    <span className="text-xs font-bold text-text">{count}</span>
                    <span className="text-[10px] text-text-muted truncate max-w-[80px]">
                      {formatType(type)}
                    </span>
                  </div>
                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block bg-background border border-border rounded px-2 py-1 text-xs text-text whitespace-nowrap z-10">
                    {formatType(type)}: {count} resources ({category})
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Vendor breakdown */}
        <div className="min-w-[140px]">
          <div className="text-[10px] text-text-dim uppercase tracking-wider mb-2">
            By Provider
          </div>
          <div className="space-y-1.5">
            {byVendor.map(([vendor, count]) => {
              const pct = (count / resources.length) * 100;
              return (
                <Link
                  key={vendor}
                  to={`/providers/${vendor}`}
                  className="flex items-center gap-2 hover:bg-surface-hover rounded px-1 -mx-1 transition-colors"
                >
                  <span className="text-xs text-text-muted w-16 truncate capitalize">
                    {vendor}
                  </span>
                  <div className="flex-1 h-4 bg-background rounded overflow-hidden min-w-[60px]">
                    <div
                      className="h-full rounded transition-all"
                      style={{
                        width: `${Math.max(pct, 4)}%`,
                        backgroundColor: vendorColor(vendor),
                      }}
                    />
                  </div>
                  <span className="text-xs font-medium text-text w-8 text-right">
                    {count}
                  </span>
                </Link>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}

/** Convert a 0..1 opacity to a 2-char hex suffix for CSS color strings. */
function opacityHex(opacity: number): string {
  return Math.round(Math.min(1, Math.max(0, opacity)) * 255)
    .toString(16)
    .padStart(2, "0");
}

const vendorColors: Record<string, string> = {
  vmware: "#60a5fa",
  aws: "#f59e0b",
  azure: "#06b6d4",
  openshift: "#ef4444",
};

function vendorColor(vendor: string): string {
  return vendorColors[vendor.toLowerCase()] || "#6366f1";
}

