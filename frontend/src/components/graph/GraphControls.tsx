interface GraphControlsProps {
  depth: number;
  onDepthChange: (depth: number) => void;
  nodeCount: number;
  edgeCount: number;
  maxNodes: number;
  totalNodes: number;
  onClose: () => void;
}

const edgeLegend = [
  { type: "DEPENDS_ON", color: "#ef4444" },
  { type: "HOSTED_ON", color: "#3b82f6" },
  { type: "MEMBER_OF", color: "#22c55e" },
  { type: "CONTAINS", color: "#a855f7" },
  { type: "CONNECTED_TO", color: "#06b6d4" },
  { type: "ATTACHED_TO", color: "#eab308" },
  { type: "MANAGES", color: "#f97316" },
  { type: "ROUTES_TO", color: "#14b8a6" },
  { type: "PEERS_WITH", color: "#ec4899" },
];

const nodeTypeLegend = [
  { type: "Virtual Machine", shape: "ellipse" },
  { type: "Hypervisor", shape: "hexagon" },
  { type: "Datastore", shape: "barrel" },
  { type: "Virtual Switch", shape: "diamond" },
  { type: "Port Group", shape: "triangle" },
  { type: "Cluster", shape: "pentagon" },
  { type: "Datacenter", shape: "round-rectangle" },
];

const shapeIcons: Record<string, string> = {
  ellipse: "●",
  hexagon: "⬡",
  barrel: "▬",
  diamond: "◆",
  triangle: "▲",
  pentagon: "⬠",
  "round-rectangle": "▮",
};

export default function GraphControls({
  depth,
  onDepthChange,
  nodeCount,
  edgeCount,
  maxNodes,
  totalNodes,
  onClose,
}: GraphControlsProps) {
  return (
    <div className="absolute top-4 right-4 bg-surface/95 border border-border rounded-lg p-4 w-56 space-y-4 z-10 max-h-[calc(100vh-120px)] overflow-y-auto">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Graph Controls</span>
        <button
          onClick={onClose}
          className="text-text-muted hover:text-text text-lg leading-none"
        >
          &times;
        </button>
      </div>

      {/* Depth slider */}
      <div>
        <label className="text-xs text-text-muted mb-1 block">
          Traversal Depth: {depth}
        </label>
        <input
          type="range"
          min={1}
          max={5}
          value={depth}
          onChange={(e) => onDepthChange(Number(e.target.value))}
          className="w-full accent-accent"
        />
        <div className="flex justify-between text-[10px] text-text-dim">
          <span>1</span>
          <span>5</span>
        </div>
      </div>

      {/* Stats */}
      <div className="text-xs text-text-muted space-y-1">
        <div>
          Nodes: {Math.min(nodeCount, maxNodes)}
          {totalNodes > maxNodes && ` of ${totalNodes}`}
        </div>
        <div>Edges: {edgeCount}</div>
      </div>

      {/* Node type legend */}
      <div>
        <div className="text-xs text-text-muted mb-1.5">Node Types</div>
        <div className="space-y-1">
          {nodeTypeLegend.map(({ type, shape }) => (
            <div key={type} className="flex items-center gap-2">
              <span className="w-3 text-center text-[10px] text-text">
                {shapeIcons[shape] || "●"}
              </span>
              <span className="text-[10px] text-text-dim">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Edge type legend */}
      <div>
        <div className="text-xs text-text-muted mb-1.5">Edge Types</div>
        <div className="space-y-1">
          {edgeLegend.map(({ type, color }) => (
            <div key={type} className="flex items-center gap-2">
              <span
                className="w-3 h-0.5 rounded"
                style={{ backgroundColor: color }}
              />
              <span className="text-[10px] text-text-dim">
                {type.replace(/_/g, " ")}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
