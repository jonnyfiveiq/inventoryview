import { useState, useEffect, useMemo } from "react";
import { CheckCircle2, XCircle, MinusCircle } from "lucide-react";
import { usePendingMatches, useReviewMatches } from "@/hooks/useAutomation";
import { useTracking } from "@/hooks/useTracking";
import type { ReviewAction } from "@/api/types";

export default function AutomationReviewPage() {
  const { track } = useTracking();

  useEffect(() => { track("Automation Metrics", "page_view"); }, []);
  const [minScore, setMinScore] = useState<number | undefined>(undefined);
  const [maxScore, setMaxScore] = useState<number | undefined>(undefined);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const { data, isLoading } = usePendingMatches({ min_score: minScore, max_score: maxScore });
  const review = useReviewMatches();

  const items = data?.items ?? [];
  const allSelected = items.length > 0 && items.every((i) => selected.has(i.id));

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(items.map((i) => i.id)));
    }
  };

  const toggleOne = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const handleBulk = (action: "approve" | "reject" | "ignore") => {
    track("Automation Metrics", "review_action_taken");
    const actions: ReviewAction[] = Array.from(selected).map((id) => ({
      pending_match_id: id,
      action,
    }));
    review.mutate(actions, {
      onSuccess: () => setSelected(new Set()),
    });
  };

  if (isLoading) {
    return <div className="text-text-muted">Loading review queue...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-text">Review Queue</h1>
        <span className="text-sm text-text-muted">{data?.total_count ?? 0} pending</span>
      </div>

      {/* Filters & bulk actions */}
      <div className="flex items-center gap-4 mb-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-xs text-text-muted">Score:</label>
          <input
            type="number"
            placeholder="Min"
            className="w-16 px-2 py-1 text-xs bg-background border border-border rounded text-text"
            value={minScore ?? ""}
            onChange={(e) => setMinScore(e.target.value ? Number(e.target.value) : undefined)}
          />
          <span className="text-text-dim">-</span>
          <input
            type="number"
            placeholder="Max"
            className="w-16 px-2 py-1 text-xs bg-background border border-border rounded text-text"
            value={maxScore ?? ""}
            onChange={(e) => setMaxScore(e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        {selected.size > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">{selected.size} selected</span>
            <button
              onClick={() => handleBulk("approve")}
              disabled={review.isPending}
              className="px-3 py-1 text-xs font-medium bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 transition-colors"
            >
              Approve Selected
            </button>
            <button
              onClick={() => handleBulk("reject")}
              disabled={review.isPending}
              className="px-3 py-1 text-xs font-medium bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-colors"
            >
              Reject Selected
            </button>
          </div>
        )}
      </div>

      {/* Table */}
      {items.length === 0 ? (
        <div className="text-center py-12 text-text-muted">
          <p>No pending matches to review.</p>
          <p className="text-xs mt-1">Upload AAP metrics data to generate matches.</p>
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-text-muted text-xs uppercase tracking-wider">
                <th className="p-3 text-left w-8">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    className="rounded border-border"
                  />
                </th>
                <th className="p-3 text-left">AAP Hostname</th>
                <th className="p-3 text-left">Suggested Resource</th>
                <th className="p-3 text-center w-20">Score</th>
                <th className="p-3 text-left">Match Reason</th>
                <th className="p-3 text-center w-32">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-border/50 hover:bg-surface-hover transition-colors">
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={selected.has(item.id)}
                      onChange={() => toggleOne(item.id)}
                      className="rounded border-border"
                    />
                  </td>
                  <td className="p-3">
                    <div className="font-medium text-text">{item.aap_host.hostname}</div>
                    <div className="text-xs text-text-dim">{item.aap_host.total_jobs} jobs</div>
                  </td>
                  <td className="p-3">
                    {item.suggested_resource ? (
                      <div>
                        <div className="text-text">{item.suggested_resource.name}</div>
                        <div className="text-xs text-text-dim capitalize">
                          {item.suggested_resource.vendor} &middot; {item.suggested_resource.normalised_type.replace(/_/g, " ")}
                        </div>
                      </div>
                    ) : (
                      <span className="text-text-dim">No suggestion</span>
                    )}
                  </td>
                  <td className="p-3 text-center">
                    <ScoreBadge score={item.match_score} />
                  </td>
                  <td className="p-3">
                    <span className="text-xs px-2 py-0.5 rounded bg-surface-hover text-text-muted">
                      {item.match_reason.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="p-3">
                    <div className="flex items-center justify-center gap-1">
                      <button
                        onClick={() =>
                          review.mutate([{ pending_match_id: item.id, action: "approve" }])
                        }
                        className="p-1.5 rounded hover:bg-green-500/20 text-text-muted hover:text-green-400 transition-colors"
                        title="Approve"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() =>
                          review.mutate([{ pending_match_id: item.id, action: "reject" }])
                        }
                        className="p-1.5 rounded hover:bg-red-500/20 text-text-muted hover:text-red-400 transition-colors"
                        title="Reject"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() =>
                          review.mutate([{ pending_match_id: item.id, action: "ignore" }])
                        }
                        className="p-1.5 rounded hover:bg-surface-hover text-text-muted transition-colors"
                        title="Ignore"
                      >
                        <MinusCircle className="w-4 h-4" />
                      </button>
                    </div>
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

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80 ? "text-green-400 bg-green-500/10" :
    score >= 50 ? "text-amber-400 bg-amber-500/10" :
    "text-red-400 bg-red-500/10";

  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded ${color}`}>
      {score}
    </span>
  );
}
