import { ChevronLeft, ChevronRight, CheckCircle, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { LoginAuditResponse } from "@/api/usage";

interface LoginAuditTableProps {
  data: LoginAuditResponse | null;
  isLoading: boolean;
  page: number;
  onPageChange: (page: number) => void;
}

export default function LoginAuditTable({
  data,
  isLoading,
  page,
  onPageChange,
}: LoginAuditTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 bg-surface border border-border rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (!data) return null;

  const totalPages = Math.ceil(data.total_count / data.page_size);

  return (
    <div>
      {/* Summary bar */}
      <div className="flex gap-6 text-sm text-text-muted mb-4 flex-wrap">
        <span>
          <strong className="text-emerald-400">{data.summary.successful}</strong> successful
        </span>
        <span>
          <strong className="text-red-400">{data.summary.failed}</strong> failed
        </span>
        <span>
          <strong className="text-text">{data.summary.unique_users}</strong> unique users
        </span>
      </div>

      {data.entries.length === 0 ? (
        <p className="text-sm text-text-muted py-4">
          No login activity for the selected period.
        </p>
      ) : (
        <div className="border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface-hover">
                <th className="text-left px-4 py-2.5 text-text-muted font-medium">Time</th>
                <th className="text-left px-4 py-2.5 text-text-muted font-medium">Username</th>
                <th className="text-left px-4 py-2.5 text-text-muted font-medium">IP Address</th>
                <th className="text-left px-4 py-2.5 text-text-muted font-medium">Outcome</th>
                <th className="text-left px-4 py-2.5 text-text-muted font-medium">Reason</th>
              </tr>
            </thead>
            <tbody>
              {data.entries.map((entry) => (
                <tr key={entry.id} className="border-t border-border">
                  <td className="px-4 py-2.5 text-text-muted text-xs whitespace-nowrap">
                    {new Date(entry.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5 text-text font-mono text-xs">{entry.username}</td>
                  <td className="px-4 py-2.5 text-text-muted font-mono text-xs">
                    {entry.ip_address}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 text-xs font-medium",
                        entry.outcome === "success" ? "text-emerald-400" : "text-red-400"
                      )}
                    >
                      {entry.outcome === "success" ? (
                        <CheckCircle className="w-3.5 h-3.5" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5" />
                      )}
                      {entry.outcome}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-text-dim text-xs">
                    {entry.failure_reason ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-3 text-sm text-text-muted">
          <span>
            Page {page} of {totalPages} ({data.total_count} total)
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="p-1 rounded hover:bg-surface-hover disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="p-1 rounded hover:bg-surface-hover disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
