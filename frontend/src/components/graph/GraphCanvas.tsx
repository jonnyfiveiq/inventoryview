import { useEffect, useRef, useCallback } from "react";
import cytoscape, { type Core, type EventObject } from "cytoscape";
import type { SubgraphResponse } from "@/api/types";

const edgeColors: Record<string, string> = {
  DEPENDS_ON: "#ef4444",
  HOSTED_ON: "#3b82f6",
  MEMBER_OF: "#22c55e",
  CONTAINS: "#a855f7",
  CONNECTED_TO: "#06b6d4",
  ATTACHED_TO: "#eab308",
  MANAGES: "#f97316",
  ROUTES_TO: "#14b8a6",
  PEERS_WITH: "#ec4899",
  SAME_ASSET: "#f59e0b",
};

const categoryColors: Record<string, string> = {
  compute: "#60a5fa",
  storage: "#f59e0b",
  network: "#22c55e",
  management: "#a855f7",
};

/** Map normalised_type to a Cytoscape node shape for visual distinction. */
const typeShapes: Record<string, string> = {
  virtual_machine: "ellipse",
  hypervisor: "hexagon",
  datastore: "barrel",
  virtual_switch: "diamond",
  port_group: "triangle",
  cluster: "round-pentagon",
  datacenter: "round-rectangle",
  resource_pool: "octagon",
  folder: "tag",
  network: "vee",
};

function formatType(ntype: string): string {
  if (!ntype) return "";
  return ntype.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

interface GraphCanvasProps {
  data: SubgraphResponse;
  centreUid: string;
  onNodeClick?: (uid: string) => void;
  onNodeExpand?: (uid: string) => void;
  maxNodes?: number;
}

export default function GraphCanvas({
  data,
  centreUid,
  onNodeClick,
  onNodeExpand,
  maxNodes = 100,
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  const initGraph = useCallback(() => {
    if (!containerRef.current) return;

    // Destroy existing instance
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const limitedNodes = data.nodes.slice(0, maxNodes);
    const nodeUids = new Set(limitedNodes.map((n) => n.uid));
    const limitedEdges = data.edges.filter(
      (e) => nodeUids.has(e.source_uid) && nodeUids.has(e.target_uid)
    );

    const elements = [
      ...limitedNodes.map((node) => ({
        data: {
          id: node.uid,
          label: node.name,
          nodeType: formatType(node.normalised_type),
          category: node.category,
          vendor: node.vendor,
          isCentre: node.uid === centreUid,
          normalised_type: node.normalised_type,
        },
      })),
      ...limitedEdges.map((edge, i) => ({
        data: {
          id: `edge-${i}`,
          source: edge.source_uid,
          target: edge.target_uid,
          label: edge.type,
          edgeType: edge.type,
        },
      })),
    ];

    const nodeCount = limitedNodes.length;
    // Scale repulsion and edge length with node count for better spacing
    const repulsion = Math.max(20000, nodeCount * 2000);
    const edgeLen = Math.max(200, nodeCount * 8);

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            label: (ele) => {
              const name = ele.data("label") || "";
              const ntype = ele.data("nodeType") || "";
              return ntype ? `${name}\n${ntype}` : name;
            },
            shape: (ele) =>
              typeShapes[ele.data("normalised_type")] || "ellipse",
            "text-valign": "bottom",
            "text-halign": "center",
            "text-wrap": "wrap",
            "text-max-width": "120px",
            "font-size": "11px",
            color: "#e4e4ef",
            "text-margin-y": 8,
            "background-color": (ele) =>
              categoryColors[ele.data("category")] || "#6b7280",
            width: 40,
            height: 40,
            "border-width": (ele) => (ele.data("isCentre") ? 3 : 1),
            "border-color": (ele) =>
              ele.data("isCentre") ? "#6366f1" : "#2a2a3a",
            "text-background-color": "#0a0a0f",
            "text-background-opacity": 0.8,
            "text-background-padding": "3px",
          } as cytoscape.Css.Node,
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
            "target-arrow-color": (ele) =>
              edgeColors[ele.data("edgeType")] || "#6b7280",
            "line-color": (ele) =>
              edgeColors[ele.data("edgeType")] || "#6b7280",
            label: "data(label)",
            "font-size": "9px",
            color: "#8888a0",
            "text-rotation": "autorotate",
            "text-margin-y": -8,
            "text-background-color": "#0a0a0f",
            "text-background-opacity": 0.7,
            "text-background-padding": "2px",
          } as cytoscape.Css.Edge,
        },
        {
          selector: "edge[edgeType = 'SAME_ASSET']",
          style: {
            "line-style": "dashed",
            "line-dash-pattern": [6, 3],
            width: 3,
            "target-arrow-shape": "none",
          } as cytoscape.Css.Edge,
        },
        {
          selector: "node:selected",
          style: {
            "border-width": 3,
            "border-color": "#6366f1",
          },
        },
      ],
      layout: {
        name: "cose",
        animate: true,
        animationDuration: 800,
        nodeRepulsion: () => repulsion,
        idealEdgeLength: () => edgeLen,
        gravity: 0.08,
        numIter: 500,
        padding: 60,
        nodeDimensionsIncludeLabels: true,
        nodeOverlap: 20,
      },
      minZoom: 0.1,
      maxZoom: 3,
      wheelSensitivity: 0.3,
    });

    // Node click events
    cy.on("tap", "node", (evt: EventObject) => {
      const nodeId = evt.target.id();
      if (nodeId === centreUid) return;

      // Check if peripheral (edge node with only 1 connection in view)
      const degree = evt.target.degree(false);
      if (degree <= 1 && onNodeExpand) {
        onNodeExpand(nodeId);
      } else if (onNodeClick) {
        onNodeClick(nodeId);
      }
    });

    cyRef.current = cy;
  }, [data, centreUid, maxNodes, onNodeClick, onNodeExpand]);

  useEffect(() => {
    initGraph();
    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [initGraph]);

  const showingLimited = data.nodes.length > maxNodes;

  return (
    <div className="relative w-full h-full">
      <div ref={containerRef} className="w-full h-full" />
      {data.nodes.length === 1 && data.edges.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="bg-surface/90 border border-border rounded-lg px-6 py-4 text-center">
            <p className="text-text-muted">No relationships found for this resource.</p>
          </div>
        </div>
      )}
      {showingLimited && (
        <div className="absolute bottom-4 left-4 bg-surface/90 border border-border rounded px-3 py-1.5 text-xs text-text-muted">
          Showing {maxNodes} of {data.nodes.length} nodes
        </div>
      )}
    </div>
  );
}
