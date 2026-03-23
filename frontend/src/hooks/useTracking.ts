import { useCallback, useRef } from "react";
import { trackEvent } from "@/api/usage";
import { useAuthStore } from "@/stores/auth";

/**
 * Hook for fire-and-forget UI usage tracking with 2-second debounce.
 *
 * Usage:
 *   const { track } = useTracking();
 *   track("Graph Visualisation", "graph_overlay_opened");
 */

const DEBOUNCE_MS = 2000;

// Module-level debounce map shared across all hook instances
const lastSent = new Map<string, number>();

export function useTracking() {
  const track = useCallback((featureArea: string, action: string) => {
    // Only track for authenticated users
    const { isAuthenticated } = useAuthStore.getState();
    if (!isAuthenticated) return;

    const key = `${featureArea}::${action}`;
    const now = Date.now();
    const prev = lastSent.get(key);

    if (prev && now - prev < DEBOUNCE_MS) return;

    lastSent.set(key, now);

    // Fire-and-forget — never block UI on tracking failures
    trackEvent(featureArea, action).catch(() => {
      // Silently ignore tracking failures per spec FR-012
    });
  }, []);

  return { track };
}
