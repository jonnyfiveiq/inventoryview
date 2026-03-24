import { useState } from "react";
import { ChevronDown, ChevronRight, RefreshCw, Shield, ShieldAlert, ShieldCheck, ShieldQuestion } from "lucide-react";
import { useResourceCorrelation, useReCorrelate } from "@/hooks/useAutomation";
import TemperatureGauge from "./TemperatureGauge";
import type { ResourceCorrelation, MatchedField } from "@/api/types";

const TIER_EXPLANATIONS: Record<string, { label: string; description: string; icon: typeof Shield }> = {
  smbios_serial: {
    label: "SMBIOS Serial Number",
    description: "Matched on hardware serial number — the most reliable identifier. This is a physical hardware property that uniquely identifies the machine.",
    icon: ShieldCheck,
  },
  bios_uuid: {
    label: "BIOS UUID",
    description: "Matched on BIOS/system UUID — a firmware-level identifier. Very reliable but can be duplicated on cloned VMs that weren't re-sysprep'd.",
    icon: ShieldCheck,
  },
  mac_address: {
    label: "MAC Address",
    description: "Matched on network interface MAC address. Reliable for physical machines but virtual NICs can be reconfigured or duplicated.",
    icon: Shield,
  },
  ip_address: {
    label: "IP Address",
    description: "Matched on IP address. Moderately reliable but IP addresses can change (DHCP) or be reassigned between hosts.",
    icon: Shield,
  },
  fqdn: {
    label: "Fully Qualified Domain Name",
    description: "Matched on FQDN from DNS. Name-based matching is less reliable — DNS records can be stale, shared, or point to different hosts over time.",
    icon: ShieldAlert,
  },
  hostname_heuristic: {
    label: "Hostname Heuristic",
    description: "Matched by normalising hostnames (stripping domain suffixes) and comparing. This is the weakest match — similar names don't guarantee the same machine.",
    icon: ShieldQuestion,
  },
  learned_mapping: {
    label: "Learned Mapping",
    description: "Previously confirmed by an operator. This match was manually reviewed and approved, creating a trusted mapping for future correlations.",
    icon: ShieldCheck,
  },
};

const CONFIDENCE_BANDS = [
  { min: 0.9, label: "Deterministic", color: "text-red-400", bg: "bg-red-500/10 border-red-500/30", verdict: "No human review needed — hardware-level certainty." },
  { min: 0.7, label: "High Confidence", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/30", verdict: "Should be validated if IPs are DHCP or NICs were replaced." },
  { min: 0.4, label: "Moderate", color: "text-yellow-400", bg: "bg-yellow-500/10 border-yellow-500/30", verdict: "Manual review recommended — name-based match is not deterministic." },
  { min: 0, label: "Low Confidence", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/30", verdict: "Weak correlation. Confirm or reject in the review queue." },
];

function getBand(confidence: number) {
  return CONFIDENCE_BANDS.find((b) => confidence >= b.min) ?? CONFIDENCE_BANDS[CONFIDENCE_BANDS.length - 1];
}

interface CorrelationDetailProps {
  resourceUid: string;
}

export default function CorrelationDetail({ resourceUid }: CorrelationDetailProps) {
  const { data, isLoading } = useResourceCorrelation(resourceUid);
  const reCorrelate = useReCorrelate();
  const [showFields, setShowFields] = useState(false);

  if (isLoading) {
    return <div className="h-24 bg-surface rounded-lg animate-pulse" />;
  }

  if (!data?.is_correlated || !data.correlation) {
    return null;
  }

  const c = data.correlation;
  const tierInfo = TIER_EXPLANATIONS[c.tier] || {
    label: c.tier.replace(/_/g, " "),
    description: "Match strategy details unavailable.",
    icon: Shield,
  };
  const band = getBand(c.confidence);
  const TierIcon = tierInfo.icon;

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold mb-3">Correlation Match</h2>
      <div className={`border rounded-lg p-5 ${band.bg}`}>
        <div className="flex items-start gap-6">
          {/* Temperature gauge */}
          <div className="shrink-0">
            <TemperatureGauge
              confidence={c.confidence}
              tier={c.tier}
              variant="thermometer"
              size="lg"
            />
          </div>

          {/* Match details */}
          <div className="flex-1 min-w-0">
            {/* Header: confidence + verdict */}
            <div className="flex items-center gap-3 mb-2">
              <span className={`text-2xl font-bold ${band.color}`}>
                {Math.round(c.confidence * 100)}%
              </span>
              <span className={`text-sm font-medium ${band.color}`}>
                {band.label}
              </span>
              {c.status === "confirmed" && (
                <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-green-500/20 text-green-400 uppercase tracking-wider">
                  Confirmed
                </span>
              )}
              {c.status === "proposed" && (
                <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 uppercase tracking-wider">
                  Proposed
                </span>
              )}
            </div>
            <p className="text-xs text-text-muted mb-3">{band.verdict}</p>

            {/* Tier explanation */}
            <div className="flex items-start gap-2 mb-3 p-3 bg-background/50 rounded">
              <TierIcon className={`w-4 h-4 mt-0.5 shrink-0 ${band.color}`} />
              <div>
                <div className="text-sm font-medium text-text">{tierInfo.label}</div>
                <p className="text-xs text-text-muted mt-0.5">{tierInfo.description}</p>
              </div>
            </div>

            {/* AAP Host */}
            <div className="text-xs text-text-muted mb-3">
              <span className="font-medium text-text">AAP Host:</span>{" "}
              <span className="font-mono">{c.aap_hostname}</span>
              {c.confirmed_by && (
                <span className="ml-2 text-text-dim">
                  Confirmed by {c.confirmed_by}
                </span>
              )}
            </div>

            {/* Matched fields toggle */}
            {c.matched_fields && c.matched_fields.length > 0 && (
              <div>
                <button
                  onClick={() => setShowFields(!showFields)}
                  className="flex items-center gap-1 text-xs text-accent hover:text-accent-hover transition-colors"
                >
                  {showFields ? (
                    <ChevronDown className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronRight className="w-3.5 h-3.5" />
                  )}
                  {showFields ? "Hide" : "Show"} matched fields ({c.matched_fields.length})
                </button>

                {showFields && (
                  <MatchedFieldsTable fields={c.matched_fields} />
                )}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="shrink-0 flex flex-col gap-2">
            <button
              onClick={() => reCorrelate.mutate(resourceUid)}
              disabled={reCorrelate.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-surface border border-border rounded hover:bg-surface-hover transition-colors text-text-muted"
              title="Re-run correlation for this resource"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${reCorrelate.isPending ? "animate-spin" : ""}`} />
              Re-correlate
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function MatchedFieldsTable({ fields }: { fields: MatchedField[] }) {
  return (
    <div className="mt-2 bg-background/50 rounded overflow-hidden">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-border/50 text-text-dim uppercase tracking-wider">
            <th className="px-3 py-2 text-left">Ansible Fact</th>
            <th className="px-3 py-2 text-left">Value</th>
            <th className="px-3 py-2 text-center w-8">&harr;</th>
            <th className="px-3 py-2 text-left">Resource Property</th>
            <th className="px-3 py-2 text-left">Value</th>
          </tr>
        </thead>
        <tbody>
          {fields.map((f, i) => (
            <tr key={i} className="border-b border-border/30 hover:bg-surface-hover/50">
              <td className="px-3 py-1.5 font-mono text-text-muted">{f.ansible_field}</td>
              <td className="px-3 py-1.5 font-mono text-text">{f.values[0]}</td>
              <td className="px-3 py-1.5 text-center text-text-dim">=</td>
              <td className="px-3 py-1.5 font-mono text-text-muted">{f.resource_field}</td>
              <td className="px-3 py-1.5 font-mono text-text">{f.values[1]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
