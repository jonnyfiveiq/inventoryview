import { HEAT_SCALE, DISCOVERY_COLOR } from "@/utils/driftColors";

export default function CalendarLegend() {
  return (
    <div className="flex items-center gap-4 text-[11px] text-text-dim mt-3">
      <div className="flex items-center gap-1.5">
        <span>Less</span>
        <div
          className="w-3 h-3 rounded-sm"
          style={{ backgroundColor: "var(--color-surface-hover, #2a2a3e)" }}
        />
        {HEAT_SCALE.map((color, i) => (
          <div
            key={i}
            className="w-3 h-3 rounded-sm"
            style={{ backgroundColor: color }}
          />
        ))}
        <span>More</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div
          className="w-3 h-3 rounded-sm"
          style={{ backgroundColor: DISCOVERY_COLOR }}
        />
        <span>Discovery</span>
      </div>
    </div>
  );
}
