import { useMemo } from "react";

type Variant = "dot" | "bar" | "thermometer";
type Size = "sm" | "md" | "lg";

interface TemperatureGaugeProps {
  confidence: number | null | undefined;
  tier?: string;
  variant: Variant;
  size?: Size;
}

const BANDS = [
  { min: 0.9, label: "Hot", color: "#ef4444", bg: "bg-red-500" },
  { min: 0.7, label: "Warm", color: "#f59e0b", bg: "bg-amber-500" },
  { min: 0.4, label: "Tepid", color: "#eab308", bg: "bg-yellow-500" },
  { min: 0, label: "Cold", color: "#3b82f6", bg: "bg-blue-500" },
] as const;

function getBand(confidence: number) {
  return BANDS.find((b) => confidence >= b.min) ?? BANDS[BANDS.length - 1];
}

const SIZE_MAP = {
  sm: { dot: 8, text: "text-[10px]", bar: "h-1.5", therm: "w-4 h-16" },
  md: { dot: 12, text: "text-xs", bar: "h-2", therm: "w-5 h-24" },
  lg: { dot: 16, text: "text-sm", bar: "h-3", therm: "w-6 h-32" },
} as const;

export default function TemperatureGauge({
  confidence,
  tier,
  variant,
  size = "md",
}: TemperatureGaugeProps) {
  const conf = confidence ?? 0;
  const band = useMemo(() => getBand(conf), [conf]);
  const pct = Math.round(conf * 100);
  const s = SIZE_MAP[size];

  if (confidence == null) {
    return (
      <span className="text-xs text-muted-foreground italic">
        No correlation data
      </span>
    );
  }

  if (variant === "dot") {
    return (
      <span className="inline-flex items-center gap-1.5">
        <span
          className="rounded-full shrink-0"
          style={{
            width: s.dot,
            height: s.dot,
            backgroundColor: band.color,
          }}
        />
        <span className={`${s.text} font-medium`}>{pct}%</span>
      </span>
    );
  }

  if (variant === "bar") {
    return (
      <div className="w-full space-y-1">
        <div className="flex items-center justify-between">
          <span className={`${s.text} font-medium`}>{band.label}</span>
          <span className={`${s.text} text-muted-foreground`}>{pct}%</span>
        </div>
        <div className={`w-full ${s.bar} rounded-full bg-secondary overflow-hidden`}>
          <div
            className={`${s.bar} rounded-full transition-all duration-500 ease-out`}
            style={{ width: `${pct}%`, backgroundColor: band.color }}
          />
        </div>
        {tier && (
          <span className="text-[10px] text-muted-foreground">{tier}</span>
        )}
      </div>
    );
  }

  // variant === "thermometer"
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className={`${s.therm} relative rounded-full overflow-hidden border border-border`}
        style={{ backgroundColor: "var(--secondary)" }}
      >
        <div
          className="absolute bottom-0 left-0 w-full rounded-full transition-all duration-700 ease-out"
          style={{
            height: `${pct}%`,
            backgroundColor: band.color,
          }}
        />
      </div>
      <span className={`${s.text} font-bold`} style={{ color: band.color }}>
        {pct}%
      </span>
      <span className={`text-[10px] text-muted-foreground`}>{band.label}</span>
      {tier && (
        <span className="text-[10px] text-muted-foreground italic">{tier}</span>
      )}
    </div>
  );
}
