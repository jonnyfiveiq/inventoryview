import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Link2, ArrowRight } from "lucide-react";
import type { AssetChainNode, AssetChainEdge } from "@/api/types";

interface AssetChainFlowProps {
  nodes: AssetChainNode[];
  edges: AssetChainEdge[];
  currentUid: string;
}

const vendorColors: Record<string, string> = {
  vmware: "#60a5fa",
  aws: "#f59e0b",
  azure: "#06b6d4",
  openshift: "#ef4444",
  kubernetes: "#326ce5",
  aap: "#10b981",
};

/**
 * Order the chain nodes into a linear sequence by walking edges.
 * The "lowest layer" (e.g. physical / VM) is placed first,
 * and the "highest layer" (e.g. application / container platform) last.
 *
 * Heuristic: nodes with fewer outgoing SAME_ASSET edges and a more
 * "infrastructure" type tend to be lower in the stack.
 */
function orderChain(
  nodes: AssetChainNode[],
  edges: AssetChainEdge[],
): AssetChainNode[] {
  if (nodes.length <= 1) return nodes;

  // Build adjacency
  const adj: Record<string, Set<string>> = {};
  for (const n of nodes) adj[n.uid] = new Set();
  for (const e of edges) {
    adj[e.source_uid]?.add(e.target_uid);
    adj[e.target_uid]?.add(e.source_uid);
  }

  // Layer priority: lower number = lower in the stack (rendered first / leftmost)
  const layerPriority: Record<string, number> = {
    hypervisor: 0,
    virtual_machine: 1,
    kubernetes_node: 2,
    kubernetes_cluster: 3,
    database_instance: 4,
    application: 5,
    aap_host: 6,
  };

  // Sort nodes by layer priority, then by vendor (vmware before openshift)
  const sorted = [...nodes].sort((a, b) => {
    const pa = layerPriority[a.normalised_type] ?? 1;
    const pb = layerPriority[b.normalised_type] ?? 1;
    if (pa !== pb) return pa - pb;
    return a.vendor.localeCompare(b.vendor);
  });

  // Walk from the lowest-layer node along edges to build the ordered chain
  const ordered: AssetChainNode[] = [];
  const visited = new Set<string>();
  const queue = [sorted[0].uid];
  visited.add(sorted[0].uid);

  // BFS but insert in layer order
  while (queue.length > 0) {
    const uid = queue.shift()!;
    const node = nodes.find((n) => n.uid === uid);
    if (node) ordered.push(node);

    const neighbors = [...(adj[uid] || [])].filter((n) => !visited.has(n));
    // Sort neighbors by layer priority
    neighbors.sort((a, b) => {
      const na = nodes.find((n) => n.uid === a);
      const nb = nodes.find((n) => n.uid === b);
      const pa = layerPriority[na?.normalised_type ?? ""] ?? 1;
      const pb = layerPriority[nb?.normalised_type ?? ""] ?? 1;
      return pa - pb;
    });

    for (const n of neighbors) {
      visited.add(n);
      queue.push(n);
    }
  }

  return ordered;
}

function edgeBetween(
  a: string,
  b: string,
  edges: AssetChainEdge[],
): AssetChainEdge | undefined {
  return edges.find(
    (e) =>
      (e.source_uid === a && e.target_uid === b) ||
      (e.source_uid === b && e.target_uid === a),
  );
}

export default function AssetChainFlow({
  nodes,
  edges,
  currentUid,
}: AssetChainFlowProps) {
  const ordered = useMemo(() => orderChain(nodes, edges), [nodes, edges]);

  if (ordered.length <= 1) return null;

  return (
    <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-4">
        <Link2 className="w-5 h-5 text-amber-500" />
        <h2 className="text-base font-semibold text-amber-500">
          Asset Stack
        </h2>
        <span className="text-xs text-text-muted">
          {ordered.length} linked resources representing the same underlying asset
        </span>
      </div>

      <div className="flex items-stretch gap-0 overflow-x-auto pb-2" style={{ scrollbarWidth: "thin" }}>
        {ordered.map((node, i) => {
          const isCurrent = node.uid === currentUid;
          const color = vendorColors[node.vendor.toLowerCase()] || "#6b7280";
          const edge = i > 0 ? edgeBetween(ordered[i - 1].uid, node.uid, edges) : null;

          return (
            <div key={node.uid} className="flex items-stretch shrink-0">
              {/* Connector arrow */}
              {i > 0 && (
                <div className="flex flex-col items-center justify-center px-2 min-w-[60px]">
                  <div className="flex items-center gap-0.5">
                    <div className="h-px w-4 bg-amber-500/40" />
                    <ArrowRight className="w-3.5 h-3.5 text-amber-500/60" />
                    <div className="h-px w-4 bg-amber-500/40" />
                  </div>
                  {edge && (
                    <span className="text-[9px] text-text-dim mt-1 text-center leading-tight whitespace-nowrap">
                      {edge.matched_key.replace(/_/g, " ")}
                    </span>
                  )}
                </div>
              )}

              {/* Node card */}
              {(() => {
                const isAapHost = node.uid.startsWith("aap:");
                const cardClasses = `
                  flex flex-col rounded-lg border px-4 py-3 min-w-[180px] max-w-[220px]
                  transition-all hover:scale-[1.02]
                  ${isCurrent
                    ? "bg-surface border-amber-500/50 ring-1 ring-amber-500/30"
                    : "bg-surface border-border hover:border-amber-500/30"
                  }
                `;
                const cardContent = (
                  <>
                    {/* Vendor badge */}
                    <div className="flex items-center gap-1.5 mb-2">
                      <span
                        className="w-2 h-2 rounded-full shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      <span
                        className="text-[10px] font-semibold uppercase tracking-wider"
                        style={{ color }}
                      >
                        {node.vendor}
                      </span>
                      {isCurrent && (
                        <span className="text-[9px] text-amber-500 font-medium ml-auto">
                          current
                        </span>
                      )}
                    </div>

                    {/* Name */}
                    <span className="text-sm font-medium leading-tight truncate">
                      {node.name}
                    </span>

                    {/* Type + state */}
                    <span className="text-[11px] text-text-muted mt-1">
                      {node.normalised_type.replace(/_/g, " ")}
                    </span>
                    {node.state && node.state !== "None" && (
                      <span className="text-[10px] text-text-dim mt-0.5">
                        {node.state}
                      </span>
                    )}
                  </>
                );

                return isAapHost ? (
                  <div className={cardClasses}>{cardContent}</div>
                ) : (
                  <Link to={`/resources/${node.uid}`} className={cardClasses}>
                    {cardContent}
                  </Link>
                );
              })()}
            </div>
          );
        })}
      </div>
    </div>
  );
}
