import { useMemo } from "react";
import { scaleSequential } from "d3-scale";
import { interpolateYlOrRd, interpolateBlues } from "d3-scale-chromatic";
import type { Resource } from "@/api/types";

interface HeatmapDetailProps {
  resources: Resource[];
}

export default function HeatmapDetail({ resources }: HeatmapDetailProps) {
  const { categories, states, recentlyChanged } = useMemo(() => {
    const catCounts: Record<string, number> = {};
    const stateCounts: Record<string, number> = {};

    for (const r of resources) {
      catCounts[r.category] = (catCounts[r.category] || 0) + 1;
      if (r.state) stateCounts[r.state] = (stateCounts[r.state] || 0) + 1;
    }

    const sorted = [...resources].sort(
      (a, b) => new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime()
    );

    return {
      categories: Object.entries(catCounts).sort((a, b) => b[1] - a[1]),
      states: Object.entries(stateCounts).sort((a, b) => b[1] - a[1]),
      recentlyChanged: sorted.slice(0, 20),
    };
  }, [resources]);

  const maxCat = Math.max(...categories.map(([, c]) => c), 1);
  const catScale = scaleSequential(interpolateYlOrRd).domain([0, maxCat]);

  const maxState = Math.max(...states.map(([, c]) => c), 1);
  const stateScale = scaleSequential(interpolateBlues).domain([0, maxState]);

  const now = Date.now();
  const dayMs = 86400000;

  return (
    <div className="space-y-8">
      {/* Category Heatmap */}
      <section>
        <h3 className="text-lg font-semibold mb-4">Resource Counts by Category</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {categories.map(([cat, count]) => (
            <div
              key={cat}
              className="relative group rounded-lg p-4 text-center"
              style={{
                backgroundColor: catScale(count),
                color: count > maxCat * 0.5 ? "#000" : "#fff",
              }}
            >
              <div className="text-3xl font-bold">{count}</div>
              <div className="text-sm opacity-80 capitalize">{cat}</div>
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block bg-background border border-border rounded px-3 py-2 text-xs text-text whitespace-nowrap z-10">
                {cat}: {count} resources ({((count / resources.length) * 100).toFixed(1)}%)
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* State Distribution */}
      <section>
        <h3 className="text-lg font-semibold mb-4">State Distribution</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {states.map(([state, count]) => (
            <div
              key={state}
              className="relative group rounded-lg p-4 text-center"
              style={{
                backgroundColor: stateScale(count),
                color: count > maxState * 0.5 ? "#000" : "#fff",
              }}
            >
              <div className="text-2xl font-bold">{count}</div>
              <div className="text-sm opacity-80">{state}</div>
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block bg-background border border-border rounded px-3 py-2 text-xs text-text whitespace-nowrap z-10">
                {state}: {count} resources ({((count / resources.length) * 100).toFixed(1)}%)
              </div>
            </div>
          ))}
        </div>
      </section>

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
