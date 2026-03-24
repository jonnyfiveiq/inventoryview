import { useSearchParams, Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck, Shield, ShieldAlert, ShieldQuestion, ShieldOff } from "lucide-react";
import { useResourcesByConfidence } from "@/hooks/useAutomation";
import ErrorBanner from "@/components/layout/ErrorBanner";
import type { BucketResource } from "@/api/automations";
import { cn } from "@/lib/utils";

const BUCKET_META: Record<string, {
  title: string;
  description: string;
  icon: typeof Shield;
  color: string;
  bg: string;
}> = {
  deterministic: {
    title: "Deterministic (>=90%)",
    description: "Hardware serial or UUID match -- highest certainty, no review needed",
    icon: ShieldCheck,
    color: "text-red-400",
    bg: "bg-red-500/10",
  },
  high: {
    title: "High (75-89%)",
    description: "Network identity match (IP/MAC) -- reliable for stable infrastructure",
    icon: Shield,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
  moderate: {
    title: "Moderate (50-74%)",
    description: "Name-based match (FQDN) -- reasonable but not deterministic",
    icon: ShieldAlert,
    color: "text-yellow-400",
    bg: "bg-yellow-500/10",
  },
  low: {
    title: "Low (<50%)",
    description: "Weak match -- hostname heuristic only, needs manual review",
    icon: ShieldQuestion,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  unmatched: {
    title: "Unmatched",
    description: "No automation correlation found for these resources",
    icon: ShieldOff,
    color: "text-zinc-400",
    bg: "bg-zinc-500/10",
  },
};

const stateColors: Record<string, string> = {
  poweredOn: "text-state-on",
  running: "text-state-on",
  connected: "text-state-connected",
  poweredOff: "text-state-off",
  stopped: "text-state-off",
  maintenance: "text-state-maintenance",
};

function ResourceRow({ resource }: { resource: BucketResource }) {
  return (
    <tr className="border-b border-border/50 hover:bg-surface-hover transition-colors">
      <td className="px-4 py-3">
        <Link
          to={`/resources/${resource.uid}`}
          className="text-accent hover:text-accent-hover font-medium"
        >
          {resource.name}
        </Link>
      </td>
      <td className="px-4 py-3 text-text-muted capitalize">{resource.vendor}</td>
      <td className="px-4 py-3 text-text-muted">{resource.normalised_type}</td>
      <td className="px-4 py-3 text-text-muted">{resource.category}</td>
      <td className={cn("px-4 py-3", stateColors[resource.state ?? ""] || "text-text-dim")}>
        {resource.state ?? "unknown"}
      </td>
      <td className="px-4 py-3 font-mono text-sm">
        {resource.confidence != null
          ? `${Math.round(resource.confidence * 100)}%`
          : "--"}
      </td>
      <td className="px-4 py-3 text-text-muted text-sm">
        {resource.tier?.replace(/_/g, " ") ?? "--"}
      </td>
    </tr>
  );
}

export default function CorrelationResourcesPage() {
  const [searchParams] = useSearchParams();
  const bucket = searchParams.get("bucket") ?? "unmatched";
  const meta = BUCKET_META[bucket] ?? BUCKET_META.unmatched;
  const Icon = meta.icon;

  const { data, isLoading, error } = useResourcesByConfidence(bucket);

  return (
    <div>
      <Link to="/" className="flex items-center gap-1 text-sm text-text-muted hover:text-text mb-4">
        <ArrowLeft className="w-4 h-4" /> Dashboard
      </Link>

      <div className={`rounded-lg border p-5 mb-6 ${meta.bg} border-border`}>
        <div className="flex items-center gap-3 mb-2">
          <Icon className={`w-6 h-6 ${meta.color}`} />
          <h1 className={`text-xl font-bold ${meta.color}`}>{meta.title}</h1>
          {data && (
            <span className="text-sm text-text-muted">
              ({data.count} resource{data.count !== 1 ? "s" : ""})
            </span>
          )}
        </div>
        <p className="text-sm text-text-muted">{meta.description}</p>
      </div>

      {/* Bucket navigation */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {Object.entries(BUCKET_META).map(([key, m]) => {
          const BIcon = m.icon;
          const active = key === bucket;
          return (
            <Link
              key={key}
              to={`/correlation/resources?bucket=${key}`}
              className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap",
                active
                  ? `${m.bg} ${m.color} border border-current/30`
                  : "bg-surface border border-border text-text-muted hover:bg-surface-hover"
              )}
            >
              <BIcon className="w-3.5 h-3.5" />
              {m.title.split(" (")[0]}
            </Link>
          );
        })}
      </div>

      {isLoading && (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-surface rounded animate-pulse" />
          ))}
        </div>
      )}

      {error && <ErrorBanner message="Failed to load resources for this confidence bucket." />}

      {data && data.resources.length === 0 && (
        <div className="text-center py-12 text-text-muted">
          No resources in this confidence bucket.
        </div>
      )}

      {data && data.resources.length > 0 && (
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-text-muted">
                <th className="text-left px-4 py-2.5 font-medium">Name</th>
                <th className="text-left px-4 py-2.5 font-medium">Vendor</th>
                <th className="text-left px-4 py-2.5 font-medium">Type</th>
                <th className="text-left px-4 py-2.5 font-medium">Category</th>
                <th className="text-left px-4 py-2.5 font-medium">State</th>
                <th className="text-left px-4 py-2.5 font-medium">Confidence</th>
                <th className="text-left px-4 py-2.5 font-medium">Tier</th>
              </tr>
            </thead>
            <tbody>
              {data.resources.map((r) => (
                <ResourceRow key={r.uid} resource={r} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
