import { ChevronLeft, ChevronRight } from "lucide-react";

interface CalendarNavProps {
  startDate: string;
  endDate: string;
  onPeriodChange: (start: string, end: string) => void;
}

function formatRange(start: string, end: string): string {
  const s = new Date(start + "T00:00:00");
  const e = new Date(end + "T00:00:00");
  const fmt = (d: Date) =>
    d.toLocaleDateString(undefined, { year: "numeric", month: "short" });
  return `${fmt(s)} – ${fmt(e)}`;
}

function shiftDates(start: string, end: string, days: number): [string, string] {
  const s = new Date(start + "T00:00:00");
  const e = new Date(end + "T00:00:00");
  s.setDate(s.getDate() + days);
  e.setDate(e.getDate() + days);
  return [s.toISOString().slice(0, 10), e.toISOString().slice(0, 10)];
}

export default function CalendarNav({ startDate, endDate, onPeriodChange }: CalendarNavProps) {
  const today = new Date().toISOString().slice(0, 10);
  const isAtPresent = endDate >= today;

  return (
    <div className="flex items-center gap-3 mb-2">
      <button
        onClick={() => {
          const [s, e] = shiftDates(startDate, endDate, -365);
          onPeriodChange(s, e);
        }}
        className="p-1 rounded hover:bg-surface-hover text-text-muted hover:text-text transition-colors"
        title="Previous year"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>
      <span className="text-xs text-text-muted font-medium">
        {formatRange(startDate, endDate)}
      </span>
      <button
        onClick={() => {
          if (!isAtPresent) {
            const [s, e] = shiftDates(startDate, endDate, 365);
            onPeriodChange(s, e);
          }
        }}
        className="p-1 rounded hover:bg-surface-hover text-text-muted hover:text-text transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
        disabled={isAtPresent}
        title="Next year"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}
