import { useState } from "react";
import { cn } from "@/lib/utils";

interface TimeRangeFilterProps {
  startDate: string;
  endDate: string;
  onRangeChange: (start: string, end: string) => void;
}

const PRESETS = [
  { label: "24h", days: 1 },
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
] as const;

function formatDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return formatDate(d);
}

export default function TimeRangeFilter({
  startDate,
  endDate,
  onRangeChange,
}: TimeRangeFilterProps) {
  const [showCustom, setShowCustom] = useState(false);
  const today = formatDate(new Date());

  // Determine which preset is active
  const activeDays = Math.round(
    (new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24)
  );
  const activePreset = PRESETS.find((p) => p.days === activeDays && endDate === today);

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {PRESETS.map((preset) => (
        <button
          key={preset.label}
          onClick={() => {
            setShowCustom(false);
            onRangeChange(daysAgo(preset.days), today);
          }}
          className={cn(
            "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
            activePreset?.label === preset.label
              ? "bg-accent text-white"
              : "bg-surface-hover text-text-muted hover:text-text"
          )}
        >
          {preset.label}
        </button>
      ))}

      <button
        onClick={() => setShowCustom(!showCustom)}
        className={cn(
          "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
          showCustom || (!activePreset && startDate)
            ? "bg-accent text-white"
            : "bg-surface-hover text-text-muted hover:text-text"
        )}
      >
        Custom
      </button>

      {showCustom && (
        <div className="flex items-center gap-2 ml-2">
          <input
            type="date"
            value={startDate}
            onChange={(e) => onRangeChange(e.target.value, endDate)}
            className="bg-surface border border-border rounded px-2 py-1 text-sm text-text"
          />
          <span className="text-text-muted text-sm">to</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => onRangeChange(startDate, e.target.value)}
            className="bg-surface border border-border rounded px-2 py-1 text-sm text-text"
          />
        </div>
      )}
    </div>
  );
}
