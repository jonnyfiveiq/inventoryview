import { useState, useEffect, useCallback } from "react";
import { Upload, FileArchive, CheckCircle2, AlertCircle } from "lucide-react";
import { useUploadMetrics } from "@/hooks/useAutomation";
import { useTracking } from "@/hooks/useTracking";
import type { UploadResponse } from "@/api/types";

export default function AutomationUploadPage() {
  const { track } = useTracking();
  const [dragOver, setDragOver] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const upload = useUploadMetrics();

  useEffect(() => { track("Automation Metrics", "page_view"); }, []);

  const handleFile = useCallback(
    (file: File) => {
      const name = file.name.toLowerCase();
      if (!name.endsWith(".zip") && !name.endsWith(".tar.gz") && !name.endsWith(".tgz")) {
        return;
      }
      setResult(null);
      track("Automation Metrics", "metrics_uploaded");
      upload.mutate(
        { file },
        { onSuccess: (data) => setResult(data) },
      );
    },
    [upload],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-xl font-bold text-text mb-6">Upload AAP Metrics Data</h1>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`
          border-2 border-dashed rounded-lg p-12 text-center transition-colors cursor-pointer
          ${dragOver ? "border-accent bg-accent/5" : "border-border hover:border-text-muted"}
          ${upload.isPending ? "opacity-50 pointer-events-none" : ""}
        `}
        onClick={() => {
          const input = document.createElement("input");
          input.type = "file";
          input.accept = ".zip,.tar.gz,.tgz";
          input.onchange = (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) handleFile(file);
          };
          input.click();
        }}
      >
        {upload.isPending ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-text-muted">Uploading and processing...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="w-10 h-10 text-text-muted" />
            <p className="text-sm text-text">Drop a metrics utility archive here or click to browse</p>
            <p className="text-xs text-text-dim">Supports .zip and .tar.gz (max 200MB)</p>
          </div>
        )}
      </div>

      {/* Error */}
      {upload.isError && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-400">Upload failed</p>
            <p className="text-xs text-text-muted mt-1">
              {(upload.error as Error)?.message || "Unknown error"}
            </p>
          </div>
        </div>
      )}

      {/* Success */}
      {result && (
        <div className="mt-6 bg-surface border border-border rounded-lg p-5">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-5 h-5 text-green-400" />
            <h2 className="text-sm font-semibold text-text">Import Complete</h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4">
            <Stat label="Hosts Imported" value={result.hosts_imported} />
            <Stat label="Hosts Updated" value={result.hosts_updated} />
            <Stat label="Jobs Imported" value={result.jobs_imported} />
            <Stat label="Events Counted" value={result.events_counted} />
            <Stat label="Indirect Nodes" value={result.indirect_nodes_imported} />
            <Stat label="Source" value={result.source_label} text />
          </div>

          {result.correlation_summary && (
            <div className="border-t border-border pt-4 mt-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
                Correlation Results
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <Stat label="Auto-Matched" value={result.correlation_summary.auto_matched} accent />
                <Stat label="Pending Review" value={result.correlation_summary.pending_review} warn />
                <Stat label="Unmatched" value={result.correlation_summary.unmatched} />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  text,
  accent,
  warn,
}: {
  label: string;
  value: number | string;
  text?: boolean;
  accent?: boolean;
  warn?: boolean;
}) {
  return (
    <div>
      <div className="text-[10px] text-text-dim uppercase tracking-wider">{label}</div>
      <div
        className={`text-lg font-bold ${
          accent ? "text-green-400" : warn ? "text-amber-400" : "text-text"
        } ${text ? "text-sm" : ""}`}
      >
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
    </div>
  );
}
