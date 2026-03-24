import { Link } from "react-router-dom";
import { ShieldCheck, Shield, ShieldAlert, ShieldQuestion, ShieldOff } from "lucide-react";
import { useFleetTemperature } from "@/hooks/useAutomation";
import type { ConfidenceBucket } from "@/api/types";

const BUCKET_STYLES: Record<string, {
  icon: typeof Shield;
  bg: string;
  border: string;
  text: string;
  accent: string;
  key: string;
}> = {
  "Deterministic (≥90%)": {
    icon: ShieldCheck,
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    text: "text-red-400",
    accent: "text-red-300",
    key: "deterministic",
  },
  "High (75–89%)": {
    icon: Shield,
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    text: "text-amber-400",
    accent: "text-amber-300",
    key: "high",
  },
  "Moderate (50–74%)": {
    icon: ShieldAlert,
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/30",
    text: "text-yellow-400",
    accent: "text-yellow-300",
    key: "moderate",
  },
  "Low (<50%)": {
    icon: ShieldQuestion,
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    text: "text-blue-400",
    accent: "text-blue-300",
    key: "low",
  },
  "Unmatched": {
    icon: ShieldOff,
    bg: "bg-zinc-500/10",
    border: "border-zinc-500/30",
    text: "text-zinc-400",
    accent: "text-zinc-300",
    key: "unmatched",
  },
};

function BucketTile({ bucket }: { bucket: ConfidenceBucket }) {
  const style = BUCKET_STYLES[bucket.label] ?? BUCKET_STYLES["Unmatched"];
  const Icon = style.icon;

  return (
    <Link
      to={`/correlation/resources?bucket=${style.key}`}
      className={`flex-1 min-w-[140px] rounded-lg border p-4 ${style.bg} ${style.border} hover:brightness-125 transition-all cursor-pointer`}
    >
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${style.text}`} />
        <span className={`text-xs font-semibold uppercase tracking-wider ${style.text}`}>
          {bucket.label}
        </span>
      </div>
      <div className={`text-3xl font-bold ${style.accent} mb-1`}>
        {bucket.count}
      </div>
      <p className="text-[11px] text-text-muted leading-tight">
        {bucket.description}
      </p>
    </Link>
  );
}

export default function CorrelationDistribution() {
  const { data, isLoading } = useFleetTemperature();

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="h-5 w-56 bg-surface rounded animate-pulse" />
        <div className="flex gap-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex-1 h-28 bg-surface rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (!data?.confidence_buckets) {
    return null;
  }

  // Reverse so deterministic is first
  const buckets = [...data.confidence_buckets].reverse();

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">Correlation Confidence</h2>
        <Link
          to="/automations"
          className="text-xs text-accent hover:text-accent-hover transition-colors"
        >
          View all automations &rarr;
        </Link>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {buckets.map((bucket) => (
          <BucketTile key={bucket.label} bucket={bucket} />
        ))}
      </div>
    </section>
  );
}
