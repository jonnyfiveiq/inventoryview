import { useMemo } from "react";
import CalendarCell from "./CalendarCell";
import type { DriftTimelineDay } from "@/api/types";

interface CalendarGridProps {
  startDate: string;
  endDate: string;
  data: DriftTimelineDay[];
  discoveryDate?: string;
  getColor: (date: string, count: number, fields: string[]) => string;
  isDiscoveryDate: (date: string) => boolean;
  onDayClick?: (date: string) => void;
}

const CELL_SIZE = 13;
const CELL_GAP = 3;
const DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];
const DAY_LABEL_WIDTH = 30;

function getMonthLabels(startDate: string, endDate: string): { label: string; weekIndex: number }[] {
  const labels: { label: string; weekIndex: number }[] = [];
  const start = new Date(startDate + "T00:00:00");
  const end = new Date(endDate + "T00:00:00");

  // Adjust start to previous Sunday
  const adjustedStart = new Date(start);
  adjustedStart.setDate(adjustedStart.getDate() - adjustedStart.getDay());

  let lastMonth = -1;
  const current = new Date(adjustedStart);

  for (let week = 0; current <= end; week++) {
    const month = current.getMonth();
    if (month !== lastMonth) {
      labels.push({
        label: current.toLocaleDateString(undefined, { month: "short" }),
        weekIndex: week,
      });
      lastMonth = month;
    }
    current.setDate(current.getDate() + 7);
  }

  return labels;
}

export default function CalendarGrid({
  startDate,
  endDate,
  data,
  getColor,
  isDiscoveryDate,
  onDayClick,
}: CalendarGridProps) {
  const { cells, totalWeeks } = useMemo(() => {
    // Build a map of date → drift data
    const dataMap = new Map<string, DriftTimelineDay>();
    for (const d of data) {
      dataMap.set(d.date, d);
    }

    const start = new Date(startDate + "T00:00:00");
    const end = new Date(endDate + "T00:00:00");

    // Adjust start to previous Sunday
    const gridStart = new Date(start);
    gridStart.setDate(gridStart.getDate() - gridStart.getDay());

    const cells: {
      date: string;
      week: number;
      day: number;
      count: number;
      fields: string[];
      color: string;
      isDiscovery: boolean;
      inRange: boolean;
    }[] = [];

    const current = new Date(gridStart);
    let week = 0;

    while (current <= end || current.getDay() !== 0) {
      const dateStr = current.toISOString().slice(0, 10);
      const inRange = current >= start && current <= end;
      const entry = dataMap.get(dateStr);
      const count = entry?.count ?? 0;
      const fields = entry?.fields ?? [];
      const discovery = isDiscoveryDate(dateStr);
      const color = getColor(dateStr, count, fields);

      cells.push({
        date: dateStr,
        week,
        day: current.getDay(),
        count,
        fields,
        color,
        isDiscovery: discovery,
        inRange,
      });

      current.setDate(current.getDate() + 1);
      if (current.getDay() === 0) week++;

      // Safety: don't exceed 54 weeks
      if (week > 53) break;
    }

    return { cells, totalWeeks: week };
  }, [startDate, endDate, data, getColor, isDiscoveryDate]);

  const monthLabels = useMemo(() => getMonthLabels(startDate, endDate), [startDate, endDate]);

  const svgWidth = DAY_LABEL_WIDTH + totalWeeks * (CELL_SIZE + CELL_GAP);
  const svgHeight = 18 + 7 * (CELL_SIZE + CELL_GAP);

  return (
    <svg width={svgWidth} height={svgHeight} className="block">
      {/* Month labels */}
      {monthLabels.map(({ label, weekIndex }) => (
        <text
          key={`${label}-${weekIndex}`}
          x={DAY_LABEL_WIDTH + weekIndex * (CELL_SIZE + CELL_GAP)}
          y={12}
          className="fill-text-dim"
          style={{ fontSize: 10 }}
        >
          {label}
        </text>
      ))}

      {/* Day labels */}
      {DAY_LABELS.map((label, i) => (
        label && (
          <text
            key={i}
            x={0}
            y={18 + i * (CELL_SIZE + CELL_GAP) + CELL_SIZE - 2}
            className="fill-text-dim"
            style={{ fontSize: 9 }}
          >
            {label}
          </text>
        )
      ))}

      {/* Cells */}
      {cells
        .filter((c) => c.inRange)
        .map((cell) => (
          <CalendarCell
            key={cell.date}
            x={DAY_LABEL_WIDTH + cell.week * (CELL_SIZE + CELL_GAP)}
            y={18 + cell.day * (CELL_SIZE + CELL_GAP)}
            size={CELL_SIZE}
            date={cell.date}
            count={cell.count}
            fields={cell.fields}
            color={cell.color}
            isDiscovery={cell.isDiscovery}
            onClick={onDayClick}
          />
        ))}
    </svg>
  );
}
