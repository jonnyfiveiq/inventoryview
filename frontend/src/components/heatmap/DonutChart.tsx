import { useMemo, useState } from "react";

interface Segment {
  label: string;
  value: number;
  color: string;
}

interface DonutChartProps {
  title: string;
  segments: Segment[];
  size?: number;
  onSegmentClick?: (group: string, category: string) => void;
  activeCategory?: string | null;
}

const STROKE_WIDTH = 28;

export default function DonutChart({ title, segments, size = 160, onSegmentClick, activeCategory }: DonutChartProps) {
  const [hovered, setHovered] = useState<number | null>(null);
  const total = useMemo(() => segments.reduce((s, seg) => s + seg.value, 0), [segments]);
  const radius = (size - STROKE_WIDTH) / 2;
  const circumference = 2 * Math.PI * radius;

  const arcs = useMemo(() => {
    let offset = 0;
    return segments.map((seg) => {
      const pct = total > 0 ? seg.value / total : 0;
      const dash = pct * circumference;
      const gap = circumference - dash;
      const arc = { ...seg, pct, dash, gap, offset };
      offset += dash;
      return arc;
    });
  }, [segments, total, circumference]);

  return (
    <div className="flex flex-col items-center">
      <h4 className="text-sm font-semibold text-text-muted mb-3 capitalize">{title}</h4>
      <div className="relative">
        <svg width={size} height={size} className="transform -rotate-90">
          {arcs.map((arc, i) => (
            <circle
              key={arc.label}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={arc.color}
              strokeWidth={activeCategory === arc.label ? STROKE_WIDTH + 6 : STROKE_WIDTH}
              strokeDasharray={`${arc.dash} ${arc.gap}`}
              strokeDashoffset={-arc.offset}
              opacity={
                activeCategory
                  ? activeCategory === arc.label ? 1 : 0.2
                  : hovered === null || hovered === i ? 1 : 0.3
              }
              className="transition-all duration-150"
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => onSegmentClick?.(title, arc.label)}
              style={{ cursor: onSegmentClick ? "pointer" : "default" }}
            />
          ))}
          {total === 0 && (
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="currentColor"
              strokeWidth={STROKE_WIDTH}
              className="text-border"
            />
          )}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {hovered !== null ? (
            <>
              <span className="text-2xl font-bold">{arcs[hovered].value}</span>
              <span className="text-[10px] text-text-muted capitalize">{arcs[hovered].label}</span>
            </>
          ) : (
            <>
              <span className="text-2xl font-bold">{total}</span>
              <span className="text-[10px] text-text-muted">total</span>
            </>
          )}
        </div>
      </div>
      <div className="flex flex-wrap justify-center gap-x-3 gap-y-1 mt-3 max-w-[200px]">
        {arcs.map((arc, i) => (
          <div
            key={arc.label}
            className="flex items-center gap-1 text-[11px] cursor-pointer"
            onMouseEnter={() => setHovered(i)}
            onMouseLeave={() => setHovered(null)}
            onClick={() => onSegmentClick?.(title, arc.label)}
          >
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ backgroundColor: arc.color }}
            />
            <span className="text-text-muted capitalize">
              {arc.label}
              <span className="text-text font-medium ml-1">
                {arc.value}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
