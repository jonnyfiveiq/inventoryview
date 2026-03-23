import { useState, useMemo } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ListMusic, Trash2, Copy, Check, Code } from "lucide-react";
import { usePlaylist, useRemoveFromPlaylist, useUpdatePlaylist } from "@/hooks/usePlaylists";
import DriftCalendar from "@/components/drift/DriftCalendar";
import PlaylistActivityLog from "@/components/playlist/PlaylistActivityLog";
import DonutChart from "@/components/heatmap/DonutChart";
import ErrorBanner from "@/components/layout/ErrorBanner";
import { cn } from "@/lib/utils";

const stateColors: Record<string, string> = {
  poweredOn: "text-state-on",
  running: "text-state-on",
  ready: "text-state-on",
  connected: "text-state-connected",
  poweredOff: "text-state-off",
  stopped: "text-state-off",
  maintenance: "text-state-maintenance",
};

export default function PlaylistDetailPage() {
  const { identifier } = useParams<{ identifier: string }>();
  const navigate = useNavigate();
  const { data: playlist, isLoading, error } = usePlaylist(identifier!);
  const removeMutation = useRemoveFromPlaylist();
  const updatePlaylist = useUpdatePlaylist();
  const [editingName, setEditingName] = useState(false);
  const [nameValue, setNameValue] = useState("");
  const [copied, setCopied] = useState(false);
  const [showJson, setShowJson] = useState(false);
  const [jsonDetail, setJsonDetail] = useState<"summary" | "full">("summary");
  const [jsonContent, setJsonContent] = useState<string | null>(null);
  const [jsonCopied, setJsonCopied] = useState(false);
  const [activityFilterDate, setActivityFilterDate] = useState<string | undefined>();

  const VENDOR_GROUPS: Record<string, string> = {
    vmware: "Private Cloud", openshift: "Private Cloud", kubernetes: "Private Cloud",
    aws: "Public Cloud", azure: "Public Cloud", gcp: "Public Cloud",
    cisco: "Networking", juniper: "Networking", paloalto: "Networking", fortinet: "Networking",
    netapp: "Storage", pure: "Storage", dell: "Storage", emc: "Storage",
  };

  const CATEGORY_COLORS: Record<string, string> = {
    compute: "#60a5fa", storage: "#a855f7", network: "#22c55e", logical: "#f59e0b",
    management: "#ec4899", security: "#ef4444", database: "#06b6d4", identity: "#f97316",
  };

  const donutGroups = useMemo(() => {
    const resources = playlist?.resources ?? [];
    if (!resources.length) return [];
    const grouped: Record<string, Record<string, number>> = {};
    for (const r of resources) {
      const group = VENDOR_GROUPS[r.vendor] ?? "Other";
      if (!grouped[group]) grouped[group] = {};
      const cat = r.category ?? "unknown";
      grouped[group][cat] = (grouped[group][cat] ?? 0) + 1;
    }
    return Object.entries(grouped)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([group, cats]) => ({
        title: group,
        segments: Object.entries(cats)
          .sort(([, a], [, b]) => b - a)
          .map(([label, value]) => ({
            label,
            value,
            color: CATEGORY_COLORS[label] ?? "#6b7280",
          })),
      }));
  }, [playlist?.resources]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-6 w-32 bg-surface rounded animate-pulse" />
        <div className="h-8 w-64 bg-surface rounded animate-pulse" />
        <div className="h-64 bg-surface rounded-lg animate-pulse" />
      </div>
    );
  }

  if (error || !playlist) {
    return (
      <div className="space-y-4">
        <Link to="/" className="flex items-center gap-1 text-sm text-text-muted hover:text-text">
          <ArrowLeft className="w-4 h-4" /> Back
        </Link>
        <ErrorBanner message={`Playlist "${identifier}" not found.`} />
      </div>
    );
  }

  const endpointUrl = `/api/v1/playlists/${playlist.slug}`;

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(`${window.location.origin}${endpointUrl}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleNameSubmit = () => {
    if (nameValue.trim() && nameValue.trim() !== playlist.name) {
      updatePlaylist.mutate(
        { identifier: identifier!, updates: { name: nameValue.trim() } },
        {
          onSuccess: (updated) => {
            setEditingName(false);
            if (updated.slug !== identifier) {
              navigate(`/playlists/${updated.slug}`, { replace: true });
            }
          },
        },
      );
    } else {
      setEditingName(false);
    }
  };

  const handleRemove = (resourceUid: string) => {
    removeMutation.mutate({ identifier: identifier!, resourceUid });
  };

  const handleShowJson = async () => {
    setShowJson(true);
    try {
      const { getPlaylist: fetchPlaylist } = await import("@/api/playlists");
      const data = await fetchPlaylist(identifier!, jsonDetail);
      setJsonContent(JSON.stringify(data, null, 2));
    } catch {
      setJsonContent('{"error": "Failed to fetch playlist data"}');
    }
  };

  const handleJsonDetailToggle = async (detail: "summary" | "full") => {
    setJsonDetail(detail);
    try {
      const { getPlaylist: fetchPlaylist } = await import("@/api/playlists");
      const data = await fetchPlaylist(identifier!, detail);
      setJsonContent(JSON.stringify(data, null, 2));
    } catch {
      setJsonContent('{"error": "Failed to fetch playlist data"}');
    }
  };

  const handleCopyJson = () => {
    if (jsonContent) {
      navigator.clipboard.writeText(jsonContent);
      setJsonCopied(true);
      setTimeout(() => setJsonCopied(false), 2000);
    }
  };

  return (
    <div>
      <Link to="/" className="flex items-center gap-1 text-sm text-text-muted hover:text-text mb-4">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <ListMusic className="w-6 h-6 text-accent" />
            {editingName ? (
              <input
                autoFocus
                value={nameValue}
                onChange={(e) => setNameValue(e.target.value)}
                onBlur={handleNameSubmit}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleNameSubmit();
                  if (e.key === "Escape") setEditingName(false);
                }}
                className="text-2xl font-bold bg-transparent border-b-2 border-accent outline-none"
              />
            ) : (
              <h1
                className="text-2xl font-bold cursor-pointer hover:text-accent transition-colors"
                onClick={() => {
                  setEditingName(true);
                  setNameValue(playlist.name);
                }}
                title="Click to rename"
              >
                {playlist.name}
              </h1>
            )}
          </div>
          {playlist.description && (
            <p className="text-text-muted text-sm mt-1 ml-9">{playlist.description}</p>
          )}
          <p className="text-text-dim text-xs mt-1 ml-9">
            {playlist.member_count} resource{playlist.member_count !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleShowJson}
            className="flex items-center gap-2 px-4 py-2 bg-surface border border-border hover:bg-surface-hover text-text rounded-md transition-colors text-sm"
          >
            <Code className="w-4 h-4" />
            JSON
          </button>
        </div>
      </div>

      {/* Endpoint URL */}
      <div className="flex items-center gap-2 mb-6 bg-surface border border-border rounded-lg px-4 py-2">
        <span className="text-xs text-text-dim">REST Endpoint:</span>
        <code className="text-xs font-mono text-accent flex-1">{endpointUrl}</code>
        <button
          onClick={handleCopyUrl}
          className="flex items-center gap-1 px-2 py-1 text-xs text-text-muted hover:text-text rounded transition-colors"
        >
          {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      {/* Members Table */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">
          Members ({playlist.member_count})
        </h2>
        {playlist.resources.length === 0 ? (
          <div className="bg-surface border border-border rounded-lg p-8 text-center">
            <ListMusic className="w-10 h-10 text-text-dim mx-auto mb-3" />
            <p className="text-text-muted text-sm">This playlist is empty.</p>
            <p className="text-text-dim text-xs mt-1">
              Navigate to a resource and click "Add to Playlist" to get started.
            </p>
          </div>
        ) : (
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted">
                  <th className="text-left px-4 py-2.5 font-medium">Name</th>
                  <th className="text-left px-4 py-2.5 font-medium">Vendor</th>
                  <th className="text-left px-4 py-2.5 font-medium">Type</th>
                  <th className="text-left px-4 py-2.5 font-medium">Category</th>
                  <th className="text-left px-4 py-2.5 font-medium">State</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {playlist.resources.map((r) => (
                  <tr key={r.uid} className="border-b border-border/50 hover:bg-surface-hover">
                    <td className="px-4 py-2">
                      <Link
                        to={`/resources/${r.uid}`}
                        className="text-accent hover:text-accent-hover font-medium"
                      >
                        {r.name}
                      </Link>
                    </td>
                    <td className="px-4 py-2 capitalize">{r.vendor}</td>
                    <td className="px-4 py-2">{r.normalised_type?.replace(/_/g, " ")}</td>
                    <td className="px-4 py-2">{r.category}</td>
                    <td className="px-4 py-2">
                      <span className={cn(stateColors[r.state ?? ""] || "text-text-dim")}>
                        {r.state ?? "—"}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      <button
                        onClick={() => handleRemove(r.uid)}
                        className="p-1 rounded hover:bg-surface text-text-dim hover:text-red-400 transition-colors"
                        title="Remove from playlist"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Infrastructure Breakdown */}
      {donutGroups.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-3">Infrastructure Breakdown</h2>
          <div className="bg-surface border border-border rounded-lg p-6">
            <div className="flex flex-wrap justify-center gap-8">
              {donutGroups.map((g) => (
                <DonutChart key={g.title} title={g.title} segments={g.segments} size={140} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Playlist Activity */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-3">Activity</h2>
        <div className="bg-surface border border-border rounded-lg p-4 mb-4">
          <DriftCalendar
            mode="playlist"
            playlistId={identifier}
            onDayClick={(date) => setActivityFilterDate(date)}
          />
        </div>
        <div className="bg-surface border border-border rounded-lg p-4">
          <PlaylistActivityLog
            identifier={identifier!}
            filterDate={activityFilterDate}
            onClearFilter={() => setActivityFilterDate(undefined)}
          />
        </div>
      </section>

      {/* JSON Preview Modal */}
      {showJson && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-background border border-border rounded-lg w-full max-w-3xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <div className="flex items-center gap-3">
                <h3 className="font-semibold">JSON Preview</h3>
                <div className="flex items-center gap-1 bg-surface rounded-md p-0.5">
                  <button
                    onClick={() => handleJsonDetailToggle("summary")}
                    className={cn(
                      "px-2 py-1 text-xs rounded transition-colors",
                      jsonDetail === "summary"
                        ? "bg-accent text-white"
                        : "text-text-muted hover:text-text"
                    )}
                  >
                    Summary
                  </button>
                  <button
                    onClick={() => handleJsonDetailToggle("full")}
                    className={cn(
                      "px-2 py-1 text-xs rounded transition-colors",
                      jsonDetail === "full"
                        ? "bg-accent text-white"
                        : "text-text-muted hover:text-text"
                    )}
                  >
                    Full Detail
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyJson}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs bg-surface border border-border rounded hover:bg-surface-hover transition-colors"
                >
                  {jsonCopied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                  {jsonCopied ? "Copied" : "Copy"}
                </button>
                <button
                  onClick={() => setShowJson(false)}
                  className="px-3 py-1.5 text-xs text-text-muted hover:text-text transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
            <div className="px-4 pt-3 pb-2 border-b border-border/50">
              <code className="text-xs font-mono text-accent">
                GET {window.location.origin}/api/v1/playlists/{playlist?.slug}{jsonDetail === "full" ? "?detail=full" : ""}
              </code>
            </div>
            <pre className="flex-1 overflow-auto p-4 text-xs text-text-muted font-mono whitespace-pre">
              {jsonContent ?? "Loading..."}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
