import { Link } from "react-router-dom";
import { useFleetTemperature } from "@/hooks/useAutomation";
import TemperatureGauge from "./TemperatureGauge";
import { Loader2, ShieldCheck, Shield, ShieldAlert, ShieldQuestion, ShieldOff } from "lucide-react";

const CONFIDENCE_BANDS = [
  { key: "deterministic", label: "Deterministic", icon: ShieldCheck, color: "text-red-400" },
  { key: "high", label: "High", icon: Shield, color: "text-amber-400" },
  { key: "moderate", label: "Moderate", icon: ShieldAlert, color: "text-yellow-400" },
  { key: "low", label: "Low", icon: ShieldQuestion, color: "text-blue-400" },
] as const;

const TIER_TO_BUCKET: Record<string, string> = {
  smbios_serial: "deterministic",
  bios_uuid: "deterministic",
  mac_address: "high",
  ip_address: "high",
  fqdn: "moderate",
  hostname_heuristic: "low",
};

export default function FleetTemperature() {
  const { data, isLoading, error } = useFleetTemperature();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading fleet correlation health...
      </div>
    );
  }

  if (error || !data) {
    return null;
  }

  return (
    <div className="rounded-lg border p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Fleet Correlation Health</h3>
        <span className="text-xs text-muted-foreground">
          {data.total_correlated}/{data.total_aap_hosts} hosts correlated
        </span>
      </div>

      {/* Overall gauge */}
      <TemperatureGauge
        confidence={data.weighted_average_confidence}
        variant="bar"
        size="lg"
      />

      {/* Confidence distribution */}
      <div className="grid grid-cols-4 gap-2 text-center">
        {CONFIDENCE_BANDS.map((band) => {
          const Icon = band.icon;
          const count = data.band_distribution[band.key] ?? 0;
          return (
            <Link
              key={band.key}
              to={`/correlation/resources?bucket=${band.key}`}
              className="rounded-lg p-2 hover:bg-surface-hover transition-colors"
            >
              <div className="flex items-center justify-center gap-1 mb-1">
                <Icon className={`w-3.5 h-3.5 ${band.color}`} />
              </div>
              <div className={`text-lg font-bold ${band.color}`}>
                {count}
              </div>
              <div className="text-[10px] text-muted-foreground">
                {band.label}
              </div>
            </Link>
          );
        })}
      </div>

      {/* Tier distribution */}
      {Object.keys(data.tier_distribution).length > 0 && (
        <div className="space-y-1">
          <h4 className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            By Correlation Method
          </h4>
          <div className="space-y-0.5">
            {Object.entries(data.tier_distribution)
              .sort(([, a], [, b]) => b - a)
              .map(([tier, count]) => {
                const bucket = TIER_TO_BUCKET[tier] ?? "low";
                return (
                  <Link
                    key={tier}
                    to={`/correlation/resources?bucket=${bucket}`}
                    className="flex items-center justify-between text-xs px-2 py-1 rounded hover:bg-surface-hover transition-colors"
                  >
                    <span className="text-muted-foreground capitalize">{tier.replace(/_/g, " ")}</span>
                    <span className="font-medium">{count}</span>
                  </Link>
                );
              })}
          </div>
        </div>
      )}

      {data.uncorrelated > 0 && (
        <Link
          to="/correlation/resources?bucket=unmatched"
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-text transition-colors"
        >
          <ShieldOff className="w-3.5 h-3.5" />
          {data.uncorrelated} host{data.uncorrelated !== 1 ? "s" : ""} uncorrelated
        </Link>
      )}
    </div>
  );
}
