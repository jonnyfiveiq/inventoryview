import { useMemo } from "react";
import { X, ArrowRight } from "lucide-react";
import { useResourceDrift } from "@/hooks/useResources";
import type { DriftEntry } from "@/api/types";

interface DriftModalProps {
  uid: string;
  resourceName: string;
  onClose: () => void;
  filterDate?: string;
}

function formatField(field: string): string {
  return field
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(val: string | null): string {
  if (val === null || val === "null" || val === "") return "—";
  return val;
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

const fieldColors: Record<string, string> = {
  state: "#22c55e",
  num_cpu: "#60a5fa",
  memory_mb: "#a855f7",
  disk_gb: "#f59e0b",
  version: "#06b6d4",
  ip_address: "#ec4899",
  tools_status: "#f97316",
  cpu_cores: "#60a5fa",
};

export default function DriftModal({ uid, resourceName, onClose, filterDate }: DriftModalProps) {
  const { data, isLoading } = useResourceDrift(uid);

  // Group drift entries by date, optionally filtered to a specific day
  const grouped = useMemo(() => {
    if (!data?.data) return [];

    let entries = data.data;
    if (filterDate) {
      entries = entries.filter((e) => e.changed_at.slice(0, 10) === filterDate);
    }

    const groups: Record<string, DriftEntry[]> = {};
    for (const entry of entries) {
      const date = new Date(entry.changed_at).toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
      if (!groups[date]) groups[date] = [];
      groups[date].push(entry);
    }
    return Object.entries(groups);
  }, [data, filterDate]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-surface border border-border rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-border shrink-0">
          <div>
            <h2 className="text-lg font-semibold">
              Configuration Drift
              {filterDate && (
                <span className="text-sm font-normal text-text-muted ml-2">
                  ({new Date(filterDate + "T00:00:00").toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })})
                </span>
              )}
            </h2>
            <p className="text-sm text-text-muted mt-0.5">{resourceName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text p-1 rounded-lg hover:bg-surface-hover transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto p-5 flex-1">
          {isLoading && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 bg-background rounded animate-pulse" />
              ))}
            </div>
          )}

          {!isLoading && (!data?.data || data.data.length === 0) && (
            <p className="text-text-muted text-center py-8">No drift history recorded.</p>
          )}

          {!isLoading && grouped.length > 0 && (
            <div className="space-y-6">
              {grouped.map(([date, entries]) => (
                <div key={date}>
                  <h3 className="text-xs font-medium text-text-dim uppercase tracking-wider mb-3">
                    {date}
                  </h3>
                  <div className="space-y-2">
                    {entries.map((entry) => (
                      <div
                        key={entry.id}
                        className="bg-background border border-border/50 rounded-lg px-4 py-3 flex items-center gap-3"
                      >
                        {/* Field badge */}
                        <span
                          className="shrink-0 text-[10px] font-bold uppercase px-2 py-0.5 rounded"
                          style={{
                            backgroundColor: (fieldColors[entry.field] || "#6b7280") + "22",
                            color: fieldColors[entry.field] || "#8888a0",
                            border: `1px solid ${fieldColors[entry.field] || "#6b7280"}44`,
                          }}
                        >
                          {formatField(entry.field)}
                        </span>

                        {/* Values */}
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <span className="text-sm text-text-muted font-mono truncate">
                            {formatValue(entry.old_value)}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5 text-text-dim shrink-0" />
                          <span className="text-sm text-text font-mono font-medium truncate">
                            {formatValue(entry.new_value)}
                          </span>
                        </div>

                        {/* Timestamp */}
                        <span className="text-[11px] text-text-dim shrink-0">
                          {formatTimestamp(entry.changed_at)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
