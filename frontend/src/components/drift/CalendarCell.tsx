import { useState } from "react";
import { DISCOVERY_COLOR } from "@/utils/driftColors";

interface CalendarCellProps {
  x: number;
  y: number;
  size: number;
  date: string;
  count: number;
  fields: string[];
  color: string;
  isDiscovery: boolean;
  onClick?: (date: string) => void;
}

export default function CalendarCell({
  x,
  y,
  size,
  date,
  count,
  fields,
  color,
  isDiscovery,
  onClick,
}: CalendarCellProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const fill = isDiscovery ? DISCOVERY_COLOR : color;
  const isClickable = count > 0 || isDiscovery;
  const isEmpty = !isDiscovery && count === 0;

  const formattedDate = new Date(date + "T00:00:00").toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <g
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onClick={() => isClickable && !isDiscovery && count > 0 && onClick?.(date)}
      style={{ cursor: isClickable && !isDiscovery && count > 0 ? "pointer" : "default" }}
    >
      <rect
        x={x}
        y={y}
        width={size}
        height={size}
        rx={2}
        fill={isEmpty ? "var(--color-surface-hover, #2a2a3e)" : fill}
        stroke={isEmpty ? "none" : "rgba(255,255,255,0.06)"}
        strokeWidth={0.5}
      />
      {showTooltip && (
        <foreignObject x={x - 80} y={y - 58} width={200} height={52} style={{ pointerEvents: "none", overflow: "visible" }}>
          <div
            style={{
              background: "#1e1e2e",
              border: "1px solid #3a3a4e",
              borderRadius: 6,
              padding: "6px 10px",
              fontSize: 11,
              color: "#e0e0e0",
              whiteSpace: "nowrap",
              boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
            }}
          >
            <div style={{ fontWeight: 600 }}>{formattedDate}</div>
            {isDiscovery && <div style={{ color: DISCOVERY_COLOR }}>Discovery</div>}
            {count > 0 && (
              <div style={{ color: "#a0a0b8" }}>
                {count} drift event{count !== 1 ? "s" : ""}
                {fields.length > 0 && ` · ${fields.join(", ")}`}
              </div>
            )}
            {!isDiscovery && count === 0 && (
              <div style={{ color: "#6b6b80" }}>No activity</div>
            )}
          </div>
        </foreignObject>
      )}
    </g>
  );
}
