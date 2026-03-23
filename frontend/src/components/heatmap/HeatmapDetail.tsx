import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { interpolateYlOrRd } from "d3-scale-chromatic";
import { X } from "lucide-react";
import DonutChart from "./DonutChart";
import type { Resource } from "@/api/types";

interface HeatmapDetailProps {
  resources: Resource[];
}

/** Map vendor names to a provider group */
const VENDOR_GROUPS: Record<string, string> = {
  vmware: "Private Cloud",
  openshift: "Private Cloud",
  kubernetes: "Private Cloud",
  aws: "Public Cloud",
  azure: "Public Cloud",
  gcp: "Public Cloud",
  cisco: "Networking",
  juniper: "Networking",
  paloalto: "Networking",
  fortinet: "Networking",
  netapp: "Storage",
  pure: "Storage",
  dell: "Storage",
  emc: "Storage",
};

const CATEGORY_COLORS: Record<string, string> = {
  compute: "#60a5fa",
  storage: "#a855f7",
  network: "#22c55e",
  logical: "#f59e0b",
  management: "#ec4899",
  security: "#ef4444",
  database: "#06b6d4",
  identity: "#f97316",
};

function colorForCategory(cat: string): string {
  return CATEGORY_COLORS[cat] || "#6b7280";
}

/** Reverse lookup: group name → set of vendor names that belong to it */
function vendorsForGroup(group: string): Set<string> {
  const vendors = new Set<string>();
  for (const [vendor, g] of Object.entries(VENDOR_GROUPS)) {
    if (g === group) vendors.add(vendor);
  }
  return vendors;
}

export default function HeatmapDetail({ resources }: HeatmapDetailProps) {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<{ group: string; category: string } | null>(null);

  const { donutGroups, recentlyChanged } = useMemo(() => {
    // Group resources: providerGroup → category → count
    const grouped: Record<string, Record<string, number>> = {};

    for (const r of resources) {
      const group = VENDOR_GROUPS[r.vendor.toLowerCase()] || r.vendor;
      if (!grouped[group]) grouped[group] = {};
      grouped[group][r.category] = (grouped[group][r.category] || 0) + 1;
    }

    // Sort groups by total count descending
    const donutGroups = Object.entries(grouped)
      .map(([group, cats]) => ({
        group,
        segments: Object.entries(cats)
          .sort((a, b) => b[1] - a[1])
          .map(([cat, count]) => ({
            label: cat,
            value: count,
            color: colorForCategory(cat),
          })),
      }))
      .sort((a, b) => {
        const totalA = a.segments.reduce((s, seg) => s + seg.value, 0);
        const totalB = b.segments.reduce((s, seg) => s + seg.value, 0);
        return totalB - totalA;
      });

    const sorted = [...resources].sort(
      (a, b) => new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime()
    );

    return {
      donutGroups,
      recentlyChanged: sorted.slice(0, 20),
    };
  }, [resources]);

  const filteredResources = useMemo(() => {
    if (!filter) return [];
    const groupVendors = vendorsForGroup(filter.group);
    return resources.filter((r) => {
      const rGroup = VENDOR_GROUPS[r.vendor.toLowerCase()] || r.vendor;
      const matchesGroup = rGroup === filter.group || groupVendors.has(r.vendor.toLowerCase());
      return matchesGroup && r.category === filter.category;
    });
  }, [resources, filter]);

  const handleSegmentClick = (group: string, category: string) => {
    if (filter?.group === group && filter?.category === category) {
      setFilter(null);
    } else {
      setFilter({ group, category });
    }
  };

  const now = Date.now();
  const dayMs = 86400000;

  return (
    <div className="space-y-8">
      {/* Category Donut Charts by Provider Group */}
      <section>
        <h3 className="text-lg font-semibold mb-4">Resource Counts by Category</h3>
        <div className="bg-surface border border-border rounded-lg p-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 justify-items-center">
            {donutGroups.map(({ group, segments }) => (
              <DonutChart
                key={group}
                title={group}
                segments={segments}
                onSegmentClick={handleSegmentClick}
                activeCategory={filter?.group === group ? filter.category : null}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Filtered Resources */}
      {filter && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">
              <span className="capitalize">{filter.category}</span>
              <span className="text-text-muted font-normal"> in </span>
              <span>{filter.group}</span>
              <span className="text-text-muted font-normal text-sm ml-2">
                ({filteredResources.length} resources)
              </span>
            </h3>
            <button
              onClick={() => setFilter(null)}
              className="flex items-center gap-1 text-sm text-text-muted hover:text-text transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              Clear filter
            </button>
          </div>
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted">
                  <th className="text-left px-4 py-2.5 font-medium">Name</th>
                  <th className="text-left px-4 py-2.5 font-medium">Type</th>
                  <th className="text-left px-4 py-2.5 font-medium">Vendor</th>
                  <th className="text-left px-4 py-2.5 font-medium">State</th>
                  <th className="text-left px-4 py-2.5 font-medium">Region</th>
                </tr>
              </thead>
              <tbody>
                {filteredResources.map((r) => (
                  <tr
                    key={r.uid}
                    className="border-b border-border/50 hover:bg-surface-hover cursor-pointer"
                    onClick={() => navigate(`/resources/${r.uid}`)}
                  >
                    <td className="px-4 py-2">{r.name}</td>
                    <td className="px-4 py-2 text-text-muted">{r.normalised_type}</td>
                    <td className="px-4 py-2 text-text-muted capitalize">{r.vendor}</td>
                    <td className="px-4 py-2 text-text-muted">{r.state ?? "—"}</td>
                    <td className="px-4 py-2 text-text-muted">{r.region ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Recently Changed */}
      <section>
        <h3 className="text-lg font-semibold mb-4">Recently Changed Resources</h3>
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-text-muted">
                <th className="text-left px-4 py-2.5 font-medium">Name</th>
                <th className="text-left px-4 py-2.5 font-medium">Type</th>
                <th className="text-left px-4 py-2.5 font-medium">Vendor</th>
                <th className="text-left px-4 py-2.5 font-medium">Last Seen</th>
                <th className="text-left px-4 py-2.5 font-medium">Recency</th>
              </tr>
            </thead>
            <tbody>
              {recentlyChanged.map((r) => {
                const ageMs = now - new Date(r.last_seen).getTime();
                const ageDays = ageMs / dayMs;
                const warmth = Math.max(0, 1 - ageDays / 7); // 0-1 scale over 7 days
                return (
                  <tr key={r.uid} className="border-b border-border/50 hover:bg-surface-hover">
                    <td className="px-4 py-2">{r.name}</td>
                    <td className="px-4 py-2 text-text-muted">{r.normalised_type}</td>
                    <td className="px-4 py-2 text-text-muted">{r.vendor}</td>
                    <td className="px-4 py-2 text-text-muted">
                      {new Date(r.last_seen).toLocaleString()}
                    </td>
                    <td className="px-4 py-2">
                      <div
                        className="w-full h-3 rounded"
                        style={{
                          backgroundColor: interpolateYlOrRd(warmth),
                          opacity: 0.8,
                        }}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
