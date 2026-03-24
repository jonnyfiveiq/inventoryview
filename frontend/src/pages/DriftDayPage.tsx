import { useEffect } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, GitCommitHorizontal } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getFleetDriftDay } from "@/api/resources";
import ErrorBanner from "@/components/layout/ErrorBanner";
import { cn } from "@/lib/utils";

const stateColors: Record<string, string> = {
  poweredOn: "text-state-on",
  running: "text-state-on",
  connected: "text-state-connected",
  ready: "text-state-on",
  poweredOff: "text-state-off",
  stopped: "text-state-off",
  deallocated: "text-state-off",
  maintenance: "text-state-maintenance",
  not_ready: "text-state-maintenance",
};

export default function DriftDayPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const date = searchParams.get("date") ?? "";

  const { data, isLoading, error } = useQuery({
    queryKey: ["drift", "fleet-day", date],
    queryFn: () => getFleetDriftDay(date),
    enabled: !!date,
  });

  // If exactly one resource, redirect straight to it
  useEffect(() => {
    if (data && data.count === 1) {
      navigate(`/resources/${data.resources[0].uid}`, { replace: true });
    }
  }, [data, navigate]);

  const formattedDate = date
    ? new Date(date + "T00:00:00").toLocaleDateString(undefined, {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "";

  if (!date) {
    return <ErrorBanner message="No date specified." />;
  }

  // Don't render the list if we're about to redirect
  if (data && data.count === 1) {
    return null;
  }

  return (
    <div>
      <Link to="/" className="flex items-center gap-1 text-sm text-text-muted hover:text-text mb-4">
        <ArrowLeft className="w-4 h-4" /> Dashboard
      </Link>

      <div className="rounded-lg border p-5 mb-6 bg-accent/5 border-border">
        <div className="flex items-center gap-3 mb-2">
          <GitCommitHorizontal className="w-6 h-6 text-accent" />
          <h1 className="text-xl font-bold">Drift Activity</h1>
          {data && (
            <span className="text-sm text-text-muted">
              ({data.count} resource{data.count !== 1 ? "s" : ""})
            </span>
          )}
        </div>
        <p className="text-sm text-text-muted">{formattedDate}</p>
      </div>

      {isLoading && (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-surface rounded animate-pulse" />
          ))}
        </div>
      )}

      {error && <ErrorBanner message="Failed to load drift data for this date." />}

      {data && data.count === 0 && (
        <div className="text-center py-12 text-text-muted">
          No drift activity on this date.
        </div>
      )}

      {data && data.count > 1 && (
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-text-muted">
                <th className="text-left px-4 py-2.5 font-medium">Name</th>
                <th className="text-left px-4 py-2.5 font-medium">Vendor</th>
                <th className="text-left px-4 py-2.5 font-medium">Type</th>
                <th className="text-left px-4 py-2.5 font-medium">Category</th>
                <th className="text-left px-4 py-2.5 font-medium">State</th>
                <th className="text-left px-4 py-2.5 font-medium">Changes</th>
                <th className="text-left px-4 py-2.5 font-medium">Fields</th>
              </tr>
            </thead>
            <tbody>
              {data.resources.map((r) => (
                <tr key={r.uid} className="border-b border-border/50 hover:bg-surface-hover transition-colors">
                  <td className="px-4 py-3">
                    <Link
                      to={`/resources/${r.uid}`}
                      className="text-accent hover:text-accent-hover font-medium"
                    >
                      {r.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-text-muted capitalize">{r.vendor}</td>
                  <td className="px-4 py-3 text-text-muted">{r.normalised_type}</td>
                  <td className="px-4 py-3 text-text-muted">{r.category}</td>
                  <td className={cn("px-4 py-3", stateColors[r.state ?? ""] || "text-text-dim")}>
                    {r.state ?? "unknown"}
                  </td>
                  <td className="px-4 py-3 font-mono text-sm">{r.drift_count}</td>
                  <td className="px-4 py-3 text-text-muted text-sm">
                    {r.fields.join(", ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
