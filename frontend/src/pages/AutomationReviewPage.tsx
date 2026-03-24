import { useState, useEffect, useMemo } from "react";
import { CheckCircle2, XCircle, MinusCircle, EyeOff, ChevronDown, ChevronRight } from "lucide-react";
import { usePendingMatches, useReviewMatches } from "@/hooks/useAutomation";
import { useTracking } from "@/hooks/useTracking";
import TemperatureGauge from "@/components/automation/TemperatureGauge";
import type { ReviewAction, PendingMatchItem } from "@/api/types";

const TIER_OPTIONS = [
  { value: "", label: "All Tiers" },
  { value: "smbios_serial", label: "SMBIOS Serial" },
  { value: "bios_uuid", label: "BIOS UUID" },
  { value: "mac_address", label: "MAC Address" },
  { value: "ip_address", label: "IP Address" },
  { value: "fqdn", label: "FQDN" },
  { value: "hostname_heuristic", label: "Hostname Heuristic" },
];

export default function AutomationReviewPage() {
  const { track } = useTracking();

  useEffect(() => { track("Automation Metrics", "page_view"); }, []);
  const [minScore, setMinScore] = useState<number | undefined>(undefined);
  const [maxScore, setMaxScore] = useState<number | undefined>(undefined);
  const [tierFilter, setTierFilter] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const { data, isLoading } = usePendingMatches({
    min_score: minScore,
    max_score: maxScore,
    tier: tierFilter || undefined,
  });
  const review = useReviewMatches();

  const items = data?.items ?? [];

  // Group by ambiguity_group_id
  const { grouped, ungrouped } = useMemo(() => {
    const groups: Record<string, PendingMatchItem[]> = {};
    const singles: PendingMatchItem[] = [];
    for (const item of items) {
      if (item.ambiguity_group_id) {
        (groups[item.ambiguity_group_id] ??= []).push(item);
      } else {
        singles.push(item);
      }
    }
    return { grouped: groups, ungrouped: singles };
  }, [items]);

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

  const toggleGroup = (groupId: string) => {
    const next = new Set(expandedGroups);
    if (next.has(groupId)) next.delete(groupId);
    else next.add(groupId);
    setExpandedGroups(next);
  };

  const handleBulk = (action: ReviewAction["action"]) => {
    track("Automation Metrics", "review_action_taken");
    const actions: ReviewAction[] = Array.from(selected).map((id) => ({
      pending_match_id: id,
      action,
    }));
    review.mutate(actions, {
      onSuccess: () => setSelected(new Set()),
    });
  };

  const handleSingle = (id: string, action: ReviewAction["action"]) => {
    review.mutate([{ pending_match_id: id, action }]);
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
            step="0.1"
            min="0"
            max="1"
            className="w-16 px-2 py-1 text-xs bg-background border border-border rounded text-text"
            value={minScore ?? ""}
            onChange={(e) => setMinScore(e.target.value ? Number(e.target.value) : undefined)}
          />
          <span className="text-text-dim">-</span>
          <input
            type="number"
            placeholder="Max"
            step="0.1"
            min="0"
            max="1"
            className="w-16 px-2 py-1 text-xs bg-background border border-border rounded text-text"
            value={maxScore ?? ""}
            onChange={(e) => setMaxScore(e.target.value ? Number(e.target.value) : undefined)}
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-text-muted">Tier:</label>
          <select
            className="px-2 py-1 text-xs bg-background border border-border rounded text-text"
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
          >
            {TIER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        {selected.size > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-text-muted">{selected.size} selected</span>
            <button
              onClick={() => handleBulk("approve")}
              disabled={review.isPending}
              className="px-3 py-1 text-xs font-medium bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => handleBulk("reject")}
              disabled={review.isPending}
              className="px-3 py-1 text-xs font-medium bg-red-500/20 text-red-400 rounded hover:bg-red-500/30 transition-colors"
            >
              Reject
            </button>
            <button
              onClick={() => handleBulk("dismiss")}
              disabled={review.isPending}
              className="px-3 py-1 text-xs font-medium bg-surface-hover text-text-muted rounded hover:bg-surface-hover/80 transition-colors"
            >
              Dismiss
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
                <th className="p-3 text-center w-20">Confidence</th>
                <th className="p-3 text-center w-28">Tier</th>
                <th className="p-3 text-left">Match Reason</th>
                <th className="p-3 text-center w-40">Actions</th>
              </tr>
            </thead>
            <tbody>
              {/* Ambiguity groups */}
              {Object.entries(grouped).map(([groupId, groupItems]) => (
                <AmbiguityGroup
                  key={groupId}
                  groupId={groupId}
                  items={groupItems}
                  expanded={expandedGroups.has(groupId)}
                  onToggle={() => toggleGroup(groupId)}
                  selected={selected}
                  onToggleSelect={toggleOne}
                  onAction={handleSingle}
                />
              ))}
              {/* Ungrouped items */}
              {ungrouped.map((item) => (
                <MatchRow
                  key={item.id}
                  item={item}
                  selected={selected.has(item.id)}
                  onToggle={() => toggleOne(item.id)}
                  onAction={(action) => handleSingle(item.id, action)}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function AmbiguityGroup({
  groupId,
  items,
  expanded,
  onToggle,
  selected,
  onToggleSelect,
  onAction,
}: {
  groupId: string;
  items: PendingMatchItem[];
  expanded: boolean;
  onToggle: () => void;
  selected: Set<string>;
  onToggleSelect: (id: string) => void;
  onAction: (id: string, action: ReviewAction["action"]) => void;
}) {
  return (
    <>
      <tr
        className="border-b border-border/50 bg-amber-500/5 cursor-pointer"
        onClick={onToggle}
      >
        <td className="p-3" colSpan={7}>
          <div className="flex items-center gap-2">
            {expanded ? (
              <ChevronDown className="w-4 h-4 text-amber-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-amber-400" />
            )}
            <span className="text-xs font-semibold text-amber-400">
              Ambiguous Match ({items.length} candidates)
            </span>
            <span className="text-xs text-text-dim">
              Host: {items[0]?.aap_host.hostname}
            </span>
          </div>
        </td>
      </tr>
      {expanded &&
        items.map((item) => (
          <MatchRow
            key={item.id}
            item={item}
            selected={selected.has(item.id)}
            onToggle={() => onToggleSelect(item.id)}
            onAction={(action) => onAction(item.id, action)}
            indent
          />
        ))}
    </>
  );
}

function MatchRow({
  item,
  selected,
  onToggle,
  onAction,
  indent,
}: {
  item: PendingMatchItem;
  selected: boolean;
  onToggle: () => void;
  onAction: (action: ReviewAction["action"]) => void;
  indent?: boolean;
}) {
  const [showFields, setShowFields] = useState(false);

  return (
    <>
      <tr className={`border-b border-border/50 hover:bg-surface-hover transition-colors ${indent ? "bg-surface/50" : ""}`}>
        <td className="p-3">
          <input
            type="checkbox"
            checked={selected}
            onChange={onToggle}
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
          <TemperatureGauge
            confidence={item.match_score}
            variant="dot"
            size="sm"
          />
        </td>
        <td className="p-3 text-center">
          {item.tier && (
            <TierBadge tier={item.tier} />
          )}
        </td>
        <td className="p-3">
          <div className="flex items-center gap-1">
            <span className="text-xs px-2 py-0.5 rounded bg-surface-hover text-text-muted">
              {item.match_reason.replace(/_/g, " ")}
            </span>
            {item.matched_fields && item.matched_fields.length > 0 && (
              <button
                onClick={() => setShowFields(!showFields)}
                className="text-[10px] text-accent hover:underline"
              >
                {showFields ? "hide" : "details"}
              </button>
            )}
          </div>
        </td>
        <td className="p-3">
          <div className="flex items-center justify-center gap-1">
            <button
              onClick={() => onAction("approve")}
              className="p-1.5 rounded hover:bg-green-500/20 text-text-muted hover:text-green-400 transition-colors"
              title="Approve"
            >
              <CheckCircle2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => onAction("reject")}
              className="p-1.5 rounded hover:bg-red-500/20 text-text-muted hover:text-red-400 transition-colors"
              title="Reject"
            >
              <XCircle className="w-4 h-4" />
            </button>
            <button
              onClick={() => onAction("dismiss")}
              className="p-1.5 rounded hover:bg-surface-hover text-text-muted transition-colors"
              title="Dismiss"
            >
              <EyeOff className="w-4 h-4" />
            </button>
            <button
              onClick={() => onAction("ignore")}
              className="p-1.5 rounded hover:bg-surface-hover text-text-muted transition-colors"
              title="Ignore"
            >
              <MinusCircle className="w-4 h-4" />
            </button>
          </div>
        </td>
      </tr>
      {showFields && item.matched_fields && (
        <tr className="border-b border-border/30">
          <td colSpan={7} className="px-6 py-2 bg-surface/80">
            <div className="text-xs space-y-1">
              {item.matched_fields.map((mf, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-text-muted">{mf.ansible_field}</span>
                  <span className="text-text-dim">=</span>
                  <span className="text-text">{mf.values[0]}</span>
                  <span className="text-text-dim">&harr;</span>
                  <span className="text-text-muted">{mf.resource_field}</span>
                  <span className="text-text-dim">=</span>
                  <span className="text-text">{mf.values[1]}</span>
                </div>
              ))}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function TierBadge({ tier }: { tier: string }) {
  const tierColors: Record<string, string> = {
    smbios_serial: "bg-red-500/20 text-red-400",
    bios_uuid: "bg-orange-500/20 text-orange-400",
    mac_address: "bg-amber-500/20 text-amber-400",
    ip_address: "bg-yellow-500/20 text-yellow-400",
    fqdn: "bg-blue-500/20 text-blue-400",
    hostname_heuristic: "bg-sky-500/20 text-sky-400",
    learned_mapping: "bg-green-500/20 text-green-400",
  };

  return (
    <span className={`text-[10px] font-medium px-2 py-0.5 rounded ${tierColors[tier] || "bg-surface-hover text-text-muted"}`}>
      {tier.replace(/_/g, " ")}
    </span>
  );
}
