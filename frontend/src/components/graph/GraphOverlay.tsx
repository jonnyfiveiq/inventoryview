import { useState, useCallback } from "react";
import { useGraph } from "@/hooks/useGraph";
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
  const [depth, setDepth] = useState(1);
  const [mergedData, setMergedData] = useState<SubgraphResponse | null>(null);

  const { data, isLoading, error } = useGraph(uid, depth);

  // Use merged data if we've done expansions, otherwise use query data
  const displayData = mergedData ?? data;

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
  }, []);

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
