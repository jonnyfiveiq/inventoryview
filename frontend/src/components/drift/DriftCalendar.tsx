import { useState, useCallback, useMemo } from "react";
import { useDriftTimeline, useFleetDriftTimeline } from "@/hooks/useResources";
import { usePlaylistActivityTimeline } from "@/hooks/usePlaylists";
import { useTracking } from "@/hooks/useTracking";
import {
  computeIntensity,
  computeAbsoluteIntensity,
  computeFleetIntensity,
  intensityToColor,
} from "@/utils/driftColors";
import CalendarGrid from "./CalendarGrid";
import CalendarLegend from "./CalendarLegend";
import CalendarNav from "./CalendarNav";

interface DriftCalendarProps {
  mode: "resource" | "fleet" | "playlist";
  resourceUid?: string;
  playlistId?: string;
  onDayClick?: (date: string) => void;
  className?: string;
}

function getDefaultDates(): [string, string] {
  const end = new Date();
  const start = new Date();
  start.setDate(start.getDate() - 364);
  return [start.toISOString().slice(0, 10), end.toISOString().slice(0, 10)];
}

export default function DriftCalendar({
  mode,
  resourceUid,
  playlistId,
  onDayClick,
  className,
}: DriftCalendarProps) {
  const { track } = useTracking();
  const [defaults] = useState(getDefaultDates);
  const [startDate, setStartDate] = useState(defaults[0]);
  const [endDate, setEndDate] = useState(defaults[1]);

  const resourceTimeline = useDriftTimeline(
    mode === "resource" ? resourceUid ?? "" : "",
    startDate,
    endDate,
  );

  const fleetTimeline = useFleetDriftTimeline(startDate, endDate);

  const playlistTimeline = usePlaylistActivityTimeline(
    mode === "playlist" ? playlistId ?? "" : "",
    startDate,
    endDate,
  );

  const handlePeriodChange = useCallback((start: string, end: string) => {
    setStartDate(start);
    setEndDate(end);
  }, []);

  const isLoading =
    mode === "resource"
      ? resourceTimeline.isLoading || fleetTimeline.isLoading
      : mode === "playlist"
        ? playlistTimeline.isLoading
        : fleetTimeline.isLoading;

  const rawTimelineData =
    mode === "resource"
      ? resourceTimeline.data
      : mode === "playlist"
        ? playlistTimeline.data
        : fleetTimeline.data;

  // Normalize playlist timeline data (actions → fields) to match DriftTimelineDay shape
  const data = useMemo(() => {
    const raw = rawTimelineData?.data ?? [];
    if (mode === "playlist") {
      return raw.map((d) => ({
        date: d.date,
        count: d.count,
        fields: "actions" in d ? (d as { actions: string[] }).actions : [],
      }));
    }
    return raw as { date: string; count: number; fields: string[] }[];
  }, [rawTimelineData, mode]);

  // Compute resource's max daily count for spike normalization
  const resourceMaxDaily = useMemo(() => {
    if (mode !== "resource" || !resourceTimeline.data?.data) return 1;
    return Math.max(1, ...resourceTimeline.data.data.map((d) => d.count));
  }, [mode, resourceTimeline.data]);

  // Fleet max daily for fleet mode
  const fleetMaxDaily = useMemo(() => {
    if (!fleetTimeline.data?.data) return 1;
    return Math.max(1, ...fleetTimeline.data.data.map((d) => d.count));
  }, [fleetTimeline.data]);

  const fleetAvg = fleetTimeline.data?.fleet_avg_lifetime ?? 0;
  const totalResourcesWithDrift = fleetTimeline.data?.total_resources_with_drift ?? 0;
  const resourceLifetime = mode === "resource" ? (resourceTimeline.data?.total_drift_count ?? 0) : 0;
  const discoveryDateStr = mode === "resource" ? (resourceTimeline.data?.first_seen ?? null) : null;
  const discoveryDate = discoveryDateStr ? discoveryDateStr.slice(0, 10) : null;

  const useAbsoluteFallback = totalResourcesWithDrift < 5;

  // Playlist max daily for playlist mode
  const playlistMaxDaily = useMemo(() => {
    if (mode !== "playlist" || !playlistTimeline.data?.data) return 1;
    return Math.max(1, ...playlistTimeline.data.data.map((d) => d.count));
  }, [mode, playlistTimeline.data]);

  const getColor = useCallback(
    (_date: string, count: number, _fields: string[]) => {
      if (count === 0) return "transparent";

      if (mode === "fleet") {
        const intensity = computeFleetIntensity(count, fleetMaxDaily);
        return intensityToColor(intensity);
      }

      if (mode === "playlist") {
        const intensity = computeAbsoluteIntensity(count);
        return intensityToColor(intensity);
      }

      // Resource mode
      if (useAbsoluteFallback) {
        return intensityToColor(computeAbsoluteIntensity(count));
      }

      const intensity = computeIntensity(
        resourceLifetime,
        fleetAvg,
        count,
        resourceMaxDaily,
      );
      return intensityToColor(intensity);
    },
    [mode, fleetMaxDaily, useAbsoluteFallback, resourceLifetime, fleetAvg, resourceMaxDaily, playlistMaxDaily],
  );

  const isDiscoveryDate = useCallback(
    (date: string) => {
      if (mode !== "resource" || !discoveryDate) return false;
      return date === discoveryDate;
    },
    [mode, discoveryDate],
  );

  if (isLoading) {
    return (
      <div className={className}>
        <div className="h-[130px] bg-surface rounded-lg animate-pulse" />
      </div>
    );
  }

  return (
    <div className={className}>
      <CalendarNav
        startDate={startDate}
        endDate={endDate}
        onPeriodChange={handlePeriodChange}
      />
      <div className="overflow-x-auto">
        <CalendarGrid
          startDate={startDate}
          endDate={endDate}
          data={data}
          getColor={getColor}
          isDiscoveryDate={isDiscoveryDate}
          onDayClick={mode === "resource" || mode === "playlist" ? (date: string) => {
            track("Drift Detection", "drift_timeline_expanded");
            onDayClick?.(date);
          } : undefined}
        />
      </div>
      <CalendarLegend />
    </div>
  );
}
