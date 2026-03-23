/**
 * Two-layer colour intensity calculation for drift calendar heatmap.
 *
 * Layer 1 (base): resource lifetime drift count vs fleet average → overall warmth
 * Layer 2 (spike): daily event count vs resource's max daily count → daily prominence
 *
 * Final intensity = base * 0.4 + spike * 0.6, clamped to [0, 1]
 */

/** Discovery day cell colour (blue/teal). */
export const DISCOVERY_COLOR = "#38bdf8";

/** Colour scale from low → high intensity (5 levels). */
const HEAT_COLORS = [
  "transparent",  // level 0 — no events
  "#4ade80",      // level 1 — light green
  "#facc15",      // level 2 — yellow
  "#f97316",      // level 3 — orange
  "#ef4444",      // level 4 — red
];

/** Absolute fallback thresholds when fleet stats are insufficient (<5 resources with drift). */
const ABSOLUTE_THRESHOLDS = [0, 1, 3, 5, 8];

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Compute intensity for a single calendar cell using the two-layer model.
 *
 * @param resourceLifetimeCount - Total drift events for this resource (all time)
 * @param fleetAvgLifetime - Average total drift events per resource across fleet
 * @param dayCount - Number of drift events on this specific day
 * @param resourceMaxDailyCount - Max events on any single day for this resource
 * @returns Intensity value between 0.0 and 1.0
 */
export function computeIntensity(
  resourceLifetimeCount: number,
  fleetAvgLifetime: number,
  dayCount: number,
  resourceMaxDailyCount: number,
): number {
  if (dayCount === 0) return 0;

  const baseIntensity = fleetAvgLifetime > 0
    ? clamp(resourceLifetimeCount / fleetAvgLifetime, 0, 1)
    : 0.5; // no fleet data → neutral base

  const spikeIntensity = resourceMaxDailyCount > 0
    ? clamp(dayCount / resourceMaxDailyCount, 0, 1)
    : 0.5;

  return clamp(baseIntensity * 0.4 + spikeIntensity * 0.6, 0, 1);
}

/**
 * Compute intensity using absolute thresholds (fallback for small fleets).
 */
export function computeAbsoluteIntensity(dayCount: number): number {
  if (dayCount === 0) return 0;
  if (dayCount >= ABSOLUTE_THRESHOLDS[4]) return 1.0;
  if (dayCount >= ABSOLUTE_THRESHOLDS[3]) return 0.75;
  if (dayCount >= ABSOLUTE_THRESHOLDS[2]) return 0.5;
  return 0.25;
}

/**
 * Map an intensity value (0.0–1.0) to a hex colour string.
 */
export function intensityToColor(intensity: number): string {
  if (intensity <= 0) return HEAT_COLORS[0];
  if (intensity <= 0.25) return HEAT_COLORS[1];
  if (intensity <= 0.50) return HEAT_COLORS[2];
  if (intensity <= 0.75) return HEAT_COLORS[3];
  return HEAT_COLORS[4];
}

/**
 * Compute intensity for fleet-mode calendar (absolute percentile-based).
 */
export function computeFleetIntensity(dayCount: number, maxDailyCount: number): number {
  if (dayCount === 0 || maxDailyCount === 0) return 0;
  return clamp(dayCount / maxDailyCount, 0, 1);
}

/** Exported for legend rendering. */
export const HEAT_SCALE = HEAT_COLORS.slice(1); // exclude transparent
