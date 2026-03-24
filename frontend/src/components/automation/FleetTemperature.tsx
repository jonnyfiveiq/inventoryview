import { useFleetTemperature } from "@/hooks/useAutomation";
import TemperatureGauge from "./TemperatureGauge";
import { Loader2 } from "lucide-react";

export default function FleetTemperature() {
  const { data, isLoading, error } = useFleetTemperature();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading fleet temperature...
      </div>
    );
  }

  if (error || !data) {
    return null;
  }

  const bandColors: Record<string, string> = {
    hot: "text-red-500",
    warm: "text-amber-500",
    tepid: "text-yellow-500",
    cold: "text-blue-500",
  };

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

      {/* Band distribution */}
      <div className="grid grid-cols-4 gap-2 text-center">
        {(["hot", "warm", "tepid", "cold"] as const).map((band) => (
          <div key={band}>
            <div className={`text-lg font-bold ${bandColors[band]}`}>
              {data.band_distribution[band] ?? 0}
            </div>
            <div className="text-[10px] text-muted-foreground capitalize">
              {band}
            </div>
          </div>
        ))}
      </div>

      {/* Tier distribution */}
      {Object.keys(data.tier_distribution).length > 0 && (
        <div className="space-y-1">
          <h4 className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            By Tier
          </h4>
          <div className="space-y-0.5">
            {Object.entries(data.tier_distribution)
              .sort(([, a], [, b]) => b - a)
              .map(([tier, count]) => (
                <div
                  key={tier}
                  className="flex items-center justify-between text-xs"
                >
                  <span className="text-muted-foreground">{tier.replace(/_/g, " ")}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {data.uncorrelated > 0 && (
        <div className="text-xs text-muted-foreground">
          {data.uncorrelated} host{data.uncorrelated !== 1 ? "s" : ""} uncorrelated
        </div>
      )}
    </div>
  );
}
