import { useState, useCallback, useEffect, useMemo } from "react";
import { useGraph } from "@/hooks/useGraph";
import { useAutomationGraph } from "@/hooks/useAutomation";
import { useTracking } from "@/hooks/useTracking";
import { getResourceGraph } from "@/api/resources";
import GraphCanvas from "./GraphCanvas";
import GraphControls from "./GraphControls";
import type { SubgraphResponse } from "@/api/types";

interface GraphOverlayProps {
  uid: string;
  onClose: () => void;
}

const MAX_NODES = 100;

export default function GraphOverlay({ uid, onClose }: GraphOverlayProps) {
  const { track } = useTracking();
  const [depth, setDepth] = useState(1);
  const [mergedData, setMergedData] = useState<SubgraphResponse | null>(null);

  useEffect(() => { track("Graph Visualisation", "graph_overlay_opened"); }, []);

  const { data, isLoading, error } = useGraph(uid, depth);
  const { data: automationData } = useAutomationGraph(uid);

  // Merge automation graph data into the infrastructure graph
  const baseData = useMemo(() => {
    if (!data) return null;
    if (!automationData || (automationData.nodes.length === 0 && automationData.edges.length === 0)) {
      return data;
    }

    const existingUids = new Set(data.nodes.map((n) => n.uid));
    const automationNodes = automationData.nodes
      .filter((n) => !existingUids.has(n.id))
      .map((n) => ({
        uid: n.id,
        name: n.label,
        category: "automation",
        vendor: n.vendor ?? "aap",
        normalised_type: n.type === "AAPHost" ? "aap_host" : (n.normalised_type ?? "unknown"),
      }));

    const existingEdgeKeys = new Set(
      data.edges.map((e) => `${e.source_uid}-${e.target_uid}-${e.type}`)
    );
    const automationEdges = automationData.edges
      .filter((e) => !existingEdgeKeys.has(`${e.source}-${e.target}-${e.type}`))
      .map((e) => ({
        source_uid: e.source,
        target_uid: e.target,
        type: e.type,
        confidence: e.confidence ?? 1,
      }));

    return {
      nodes: [...data.nodes, ...automationNodes],
      edges: [...data.edges, ...automationEdges],
    };
  }, [data, automationData]);

  // Use merged data if we've done expansions, otherwise use base data
  const displayData = mergedData ?? baseData;

  const handleNodeExpand = useCallback(
    async (nodeUid: string) => {
      try {
        const expanded = await getResourceGraph(nodeUid, 1);
        const current = mergedData ?? data;
        if (!current) return;

        // Merge new nodes and edges
        const existingUids = new Set(current.nodes.map((n) => n.uid));
        const newNodes = expanded.nodes.filter((n) => !existingUids.has(n.uid));

        const existingEdgeKeys = new Set(
          current.edges.map((e) => `${e.source_uid}-${e.target_uid}-${e.type}`)
        );
        const newEdges = expanded.edges.filter(
          (e) => !existingEdgeKeys.has(`${e.source_uid}-${e.target_uid}-${e.type}`)
        );

        setMergedData({
          nodes: [...current.nodes, ...newNodes],
          edges: [...current.edges, ...newEdges],
        });
      } catch {
        // Expansion failed silently
      }
    },
    [data, mergedData]
  );

  // Reset merged data when depth changes
  const handleDepthChange = useCallback((newDepth: number) => {
    setMergedData(null);
    setDepth(newDepth);
    track("Graph Visualisation", "depth_changed");
  }, [track]);

  return (
    <div
      className="fixed inset-0 z-50 bg-background/95 flex flex-col"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-border">
        <h2 className="text-lg font-semibold">Resource Graph</h2>
        <button
          onClick={onClose}
          className="px-3 py-1 text-sm text-text-muted hover:text-text bg-surface hover:bg-surface-hover border border-border rounded-md transition-colors"
        >
          Close
        </button>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-text-muted">Loading graph...</span>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-state-error">Failed to load graph data.</span>
          </div>
        )}

        {displayData && (
          <>
            <GraphCanvas
              data={displayData}
              centreUid={uid}
              onNodeExpand={handleNodeExpand}
              maxNodes={MAX_NODES}
            />
            <GraphControls
              depth={depth}
              onDepthChange={handleDepthChange}
              nodeCount={displayData.nodes.length}
              edgeCount={displayData.edges.length}
              maxNodes={MAX_NODES}
              totalNodes={displayData.nodes.length}
              onClose={onClose}
            />
          </>
        )}
      </div>
    </div>
  );
}
