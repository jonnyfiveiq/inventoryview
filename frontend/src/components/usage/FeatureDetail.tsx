import { ArrowLeft } from "lucide-react";
import type { FeatureDetailResponse } from "@/api/usage";

interface FeatureDetailProps {
  featureArea: string;
  data: FeatureDetailResponse | null;
  isLoading: boolean;
  onBack: () => void;
}

export default function FeatureDetail({
  featureArea,
  data,
  isLoading,
  onBack,
}: FeatureDetailProps) {
  return (
    <div>
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text transition-colors mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to overview
      </button>

      <h2 className="text-lg font-semibold text-text mb-4">{featureArea}</h2>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-10 bg-surface border border-border rounded animate-pulse" />
          ))}
        </div>
      )}

      {data && data.actions.length === 0 && (
        <p className="text-sm text-text-muted py-4">
          No actions recorded for this feature area in the selected period.
        </p>
      )}

      {data && data.actions.length > 0 && (
        <div className="border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface-hover">
                <th className="text-left px-4 py-2.5 text-text-muted font-medium">Action</th>
                <th className="text-right px-4 py-2.5 text-text-muted font-medium">Count</th>
                <th className="text-right px-4 py-2.5 text-text-muted font-medium">Unique Users</th>
              </tr>
            </thead>
            <tbody>
              {data.actions.map((a) => (
                <tr key={a.action} className="border-t border-border">
                  <td className="px-4 py-2.5 text-text font-mono text-xs">{a.action}</td>
                  <td className="px-4 py-2.5 text-text text-right">{a.count.toLocaleString()}</td>
                  <td className="px-4 py-2.5 text-text-muted text-right">{a.unique_users}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t border-border bg-surface-hover">
                <td className="px-4 py-2.5 text-text font-medium">Total</td>
                <td className="px-4 py-2.5 text-text text-right font-medium">
                  {data.total_events.toLocaleString()}
                </td>
                <td />
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}
