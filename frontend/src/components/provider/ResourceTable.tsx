import { useNavigate } from "react-router-dom";
import { Network } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Resource } from "@/api/types";

const stateColors: Record<string, string> = {
  poweredOn: "text-state-on",
  running: "text-state-on",
  connected: "text-state-connected",
  poweredOff: "text-state-off",
  stopped: "text-state-off",
  disconnected: "text-state-disconnected",
  maintenance: "text-state-maintenance",
  decommissioned: "text-state-off",
  template: "text-text-dim",
};

interface ResourceTableProps {
  resources: Resource[];
  onGraphClick: (uid: string) => void;
}

export default function ResourceTable({ resources, onGraphClick }: ResourceTableProps) {
  const navigate = useNavigate();

  if (resources.length === 0) {
    return (
      <div className="text-center py-12 text-text-muted">
        <p className="text-lg mb-2">No resources match your filters</p>
        <p className="text-sm">Try adjusting or clearing the filters above.</p>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-text-muted">
            <th className="text-left px-4 py-2.5 font-medium">Name</th>
            <th className="text-left px-4 py-2.5 font-medium">Type</th>
            <th className="text-left px-4 py-2.5 font-medium">Category</th>
            <th className="text-left px-4 py-2.5 font-medium">State</th>
            <th className="text-left px-4 py-2.5 font-medium">Region</th>
            <th className="text-left px-4 py-2.5 font-medium">Last Seen</th>
            <th className="text-center px-4 py-2.5 font-medium w-16">Graph</th>
          </tr>
        </thead>
        <tbody>
          {resources.map((r) => (
            <tr
              key={r.uid}
              className="border-b border-border/50 hover:bg-surface-hover cursor-pointer transition-colors"
              onClick={() => navigate(`/resources/${r.uid}`)}
            >
              <td className="px-4 py-2.5 font-medium">{r.name}</td>
              <td className="px-4 py-2.5 text-text-muted">{r.normalised_type}</td>
              <td className="px-4 py-2.5 text-text-muted capitalize">{r.category}</td>
              <td className={cn("px-4 py-2.5", stateColors[r.state ?? ""] || "text-text-dim")}>
                {r.state ?? "—"}
              </td>
              <td className="px-4 py-2.5 text-text-muted">{r.region ?? "—"}</td>
              <td className="px-4 py-2.5 text-text-muted">
                {new Date(r.last_seen).toLocaleDateString()}
              </td>
              <td className="px-4 py-2.5 text-center">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onGraphClick(r.uid);
                  }}
                  className="p-1 rounded text-text-muted hover:text-accent hover:bg-accent/10 transition-colors"
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
  );
}
