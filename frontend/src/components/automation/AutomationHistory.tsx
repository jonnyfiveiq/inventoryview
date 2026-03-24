import { Link } from "react-router-dom";
import { Clock, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import { useAutomationHistory, useResourceCorrelation } from "@/hooks/useAutomation";
import TemperatureGauge from "./TemperatureGauge";
import type { JobExecutionItem } from "@/api/types";

interface AutomationHistoryProps {
  resourceUid: string;
}

export default function AutomationHistory({ resourceUid }: AutomationHistoryProps) {
  const { data, isLoading } = useAutomationHistory(resourceUid);
  const { data: correlation } = useResourceCorrelation(resourceUid);

  if (isLoading) {
    return <div className="h-32 bg-surface rounded-lg animate-pulse" />;
  }

  if (!data || data.total_jobs === 0) {
    return null;
  }

  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold mb-3">Automation History</h2>
      <div className="bg-surface border border-border rounded-lg p-5">
        {/* Summary */}
        <div className="flex items-center gap-6 mb-4">
          <div>
            <div className="text-[10px] text-text-dim uppercase tracking-wider">Total Jobs</div>
            <div className="text-2xl font-bold text-text">{data.total_jobs.toLocaleString()}</div>
          </div>
          {data.first_automated && (
            <div>
              <div className="text-[10px] text-text-dim uppercase tracking-wider">First Automated</div>
              <div className="text-sm text-text">{new Date(data.first_automated).toLocaleDateString()}</div>
            </div>
          )}
          {data.last_automated && (
            <div>
              <div className="text-[10px] text-text-dim uppercase tracking-wider">Last Automated</div>
              <div className="text-sm text-text">{new Date(data.last_automated).toLocaleDateString()}</div>
            </div>
          )}
        </div>

        {/* AAP Hosts */}
        {data.aap_hosts.length > 0 && (
          <div className="mb-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">
              Linked AAP Hosts
            </h3>
            <div className="flex flex-wrap gap-2">
              {data.aap_hosts.map((h) => (
                <span
                  key={h.hostname}
                  className="inline-flex items-center gap-1.5 px-2 py-1 text-xs bg-accent/10 text-accent rounded"
                >
                  {h.hostname}
                  <span className="text-text-dim capitalize">
                    ({h.correlation_type.replace(/_/g, " ")})
                  </span>
                  {correlation?.is_correlated && correlation.correlation && (
                    <TemperatureGauge
                      confidence={correlation.correlation.confidence}
                      variant="dot"
                      size="sm"
                    />
                  )}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Recent executions */}
        {data.executions.items.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">
              Recent Executions
            </h3>
            <div className="space-y-1.5">
              {data.executions.items.slice(0, 10).map((exec) => (
                <ExecutionRow key={`${exec.job_id}-${exec.executed_at}`} exec={exec} />
              ))}
            </div>
            {data.executions.total_count > 10 && (
              <div className="mt-2 text-xs text-text-dim">
                Showing 10 of {data.executions.total_count} executions
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

function ExecutionRow({ exec }: { exec: JobExecutionItem }) {
  const hasFailures = exec.failures > 0 || exec.dark > 0;
  const allOk = !hasFailures && exec.ok > 0;

  return (
    <div className="flex items-center gap-3 text-sm py-1.5 px-2 rounded hover:bg-surface-hover transition-colors">
      <Clock className="w-3.5 h-3.5 text-text-dim shrink-0" />
      <span className="text-xs text-text-dim w-24 shrink-0">
        {new Date(exec.executed_at).toLocaleDateString()}
      </span>
      <span className="text-text flex-1 truncate">{exec.job_name || `Job ${exec.job_id}`}</span>
      <div className="flex items-center gap-2 shrink-0">
        {exec.ok > 0 && (
          <span className="text-xs text-green-400">{exec.ok} ok</span>
        )}
        {exec.changed > 0 && (
          <span className="text-xs text-amber-400">{exec.changed} changed</span>
        )}
        {exec.failures > 0 && (
          <span className="text-xs text-red-400">{exec.failures} failed</span>
        )}
        {exec.dark > 0 && (
          <span className="text-xs text-red-400">{exec.dark} unreachable</span>
        )}
      </div>
      {allOk ? (
        <CheckCircle2 className="w-3.5 h-3.5 text-green-400 shrink-0" />
      ) : hasFailures ? (
        <XCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />
      ) : (
        <AlertTriangle className="w-3.5 h-3.5 text-text-dim shrink-0" />
      )}
    </div>
  );
}
