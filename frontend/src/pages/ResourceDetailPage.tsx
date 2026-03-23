import { useState, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Network, GitCompareArrows } from "lucide-react";
import { useResource, useResourceRelationships, useResourceDriftExists, useAssetChain } from "@/hooks/useResources";
import { useQueries } from "@tanstack/react-query";
import { getResource } from "@/api/resources";
import GraphOverlay from "@/components/graph/GraphOverlay";
import DriftModal from "@/components/resource/DriftModal";
import DriftCalendar from "@/components/drift/DriftCalendar";
import AssetChainFlow from "@/components/resource/AssetChainFlow";
import AddToPlaylistButton from "@/components/playlist/AddToPlaylistButton";
import ErrorBanner from "@/components/layout/ErrorBanner";
import { cn } from "@/lib/utils";

const stateColors: Record<string, string> = {
  poweredOn: "text-state-on",
  running: "text-state-on",
  connected: "text-state-connected",
  poweredOff: "text-state-off",
  stopped: "text-state-off",
  maintenance: "text-state-maintenance",
};

export default function ResourceDetailPage() {
  const { uid } = useParams<{ uid: string }>();
  const [showGraph, setShowGraph] = useState(false);
  const [showDrift, setShowDrift] = useState(false);
  const [selectedDriftDate, setSelectedDriftDate] = useState<string | undefined>();

  const { data: resource, isLoading, error } = useResource(uid!);
  const { data: relationships } = useResourceRelationships(uid!);
  const { data: driftStatus } = useResourceDriftExists(uid!);
  const { data: assetChain } = useAssetChain(uid!);

  // Collect unique related resource UIDs to resolve their names
  const relatedUids = useMemo(() => {
    if (!relationships?.data) return [];
    const uids = new Set<string>();
    for (const rel of relationships.data) {
      const relatedUid = rel.source_uid === uid ? rel.target_uid : rel.source_uid;
      uids.add(relatedUid);
    }
    return Array.from(uids);
  }, [relationships, uid]);

  const relatedQueries = useQueries({
    queries: relatedUids.map((relUid) => ({
      queryKey: ["resource", relUid],
      queryFn: () => getResource(relUid),
      enabled: !!relUid,
      staleTime: 5 * 60 * 1000,
    })),
  });

  const nameMap = useMemo(() => {
    const map: Record<string, string> = {};
    relatedQueries.forEach((q, i) => {
      if (q.data) {
        map[relatedUids[i]] = q.data.name;
      }
    });
    return map;
  }, [relatedQueries, relatedUids]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-6 w-32 bg-surface rounded animate-pulse" />
        <div className="h-8 w-64 bg-surface rounded animate-pulse" />
        <div className="h-64 bg-surface rounded-lg animate-pulse" />
      </div>
    );
  }

  if (error || !resource) {
    return (
      <div className="space-y-4">
        <Link to="/" className="flex items-center gap-1 text-sm text-text-muted hover:text-text">
          <ArrowLeft className="w-4 h-4" /> Back
        </Link>
        <ErrorBanner message={`Resource ${uid} not found.`} />
      </div>
    );
  }

  const properties = [
    { label: "UID", value: resource.uid },
    { label: "Name", value: resource.name },
    { label: "Vendor", value: resource.vendor },
    { label: "Vendor ID", value: resource.vendor_id },
    { label: "Vendor Type", value: resource.vendor_type },
    { label: "Normalised Type", value: resource.normalised_type },
    { label: "Category", value: resource.category },
    { label: "Region", value: resource.region ?? "—" },
    { label: "State", value: resource.state ?? "—" },
    { label: "First Seen", value: new Date(resource.first_seen).toLocaleString() },
    { label: "Last Seen", value: new Date(resource.last_seen).toLocaleString() },
    {
      label: "Classification",
      value: resource.classification_method
        ? `${resource.classification_method} (${((resource.classification_confidence ?? 0) * 100).toFixed(0)}%)`
        : "—",
    },
  ];

  return (
    <div>
      <Link to="/" className="flex items-center gap-1 text-sm text-text-muted hover:text-text mb-4">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{resource.name}</h1>
          <p className="text-text-muted text-sm mt-1">
            <span className="capitalize">{resource.vendor}</span> &middot;{" "}
            {resource.vendor_type} &middot;{" "}
            <span className={cn(stateColors[resource.state ?? ""] || "text-text-dim")}>
              {resource.state ?? "unknown"}
            </span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          <AddToPlaylistButton resourceUid={uid!} />
          {driftStatus?.has_drift && (
            <button
              onClick={() => setShowDrift(true)}
              className="flex items-center gap-2 px-4 py-2 bg-surface border border-border hover:bg-surface-hover text-text rounded-md transition-colors text-sm"
            >
              <GitCompareArrows className="w-4 h-4 text-state-maintenance" />
              Drift History
            </button>
          )}
          <button
            onClick={() => setShowGraph(true)}
            className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-hover text-white rounded-md transition-colors text-sm"
          >
            <Network className="w-4 h-4" />
            View Graph
          </button>
        </div>
      </div>

      {/* Asset Chain Flow */}
      {assetChain && (
        <section className="mb-8">
          <AssetChainFlow
            nodes={assetChain.nodes}
            edges={assetChain.edges}
            currentUid={uid!}
          />
        </section>
      )}

      {/* Drift Calendar */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">Drift Activity</h2>
        <div className="bg-surface border border-border rounded-lg p-4">
          <DriftCalendar
            mode="resource"
            resourceUid={uid}
            onDayClick={(date) => {
              setSelectedDriftDate(date);
              setShowDrift(true);
            }}
          />
        </div>
      </section>

      {/* Properties table */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">Properties</h2>
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <tbody>
              {properties.map(({ label, value }) => (
                <tr key={label} className="border-b border-border/50">
                  <td className="px-4 py-2.5 text-text-muted font-medium w-48">{label}</td>
                  <td className="px-4 py-2.5 font-mono text-sm">{value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Raw properties */}
      {resource.raw_properties && Object.keys(resource.raw_properties).length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-3">Raw Properties</h2>
          <div className="bg-surface border border-border rounded-lg p-4">
            <pre className="text-xs text-text-muted overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(resource.raw_properties, null, 2)}
            </pre>
          </div>
        </section>
      )}

      {/* Relationships */}
      {relationships && relationships.data.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-3">
            Relationships ({relationships.data.length})
          </h2>
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted">
                  <th className="text-left px-4 py-2.5 font-medium">Direction</th>
                  <th className="text-left px-4 py-2.5 font-medium">Type</th>
                  <th className="text-left px-4 py-2.5 font-medium">Related Resource</th>
                  <th className="text-left px-4 py-2.5 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {relationships.data.map((rel, i) => {
                  const isOutgoing = rel.source_uid === uid;
                  return (
                    <tr key={i} className="border-b border-border/50 hover:bg-surface-hover">
                      <td className="px-4 py-2 text-text-muted">
                        {isOutgoing ? "→ outgoing" : "← incoming"}
                      </td>
                      <td className="px-4 py-2 font-medium">{rel.type}</td>
                      <td className="px-4 py-2">
                        {(() => {
                          const relatedUid = isOutgoing ? rel.target_uid : rel.source_uid;
                          return (
                            <Link
                              to={`/resources/${relatedUid}`}
                              className="text-accent hover:text-accent-hover"
                            >
                              {nameMap[relatedUid] || relatedUid}
                            </Link>
                          );
                        })()}
                      </td>
                      <td className="px-4 py-2 text-text-muted">
                        {(rel.confidence * 100).toFixed(0)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {showGraph && uid && (
        <GraphOverlay uid={uid} onClose={() => setShowGraph(false)} />
      )}

      {showDrift && uid && resource && (
        <DriftModal
          uid={uid}
          resourceName={resource.name}
          filterDate={selectedDriftDate}
          onClose={() => {
            setShowDrift(false);
            setSelectedDriftDate(undefined);
          }}
        />
      )}
    </div>
  );
}
