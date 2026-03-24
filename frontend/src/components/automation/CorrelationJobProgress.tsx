import { useCorrelationJob } from "@/hooks/useAutomation";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";

interface CorrelationJobProgressProps {
  jobId: string;
  onComplete?: () => void;
}

export default function CorrelationJobProgress({
  jobId,
  onComplete,
}: CorrelationJobProgressProps) {
  const { data: job, isLoading } = useCorrelationJob(jobId, { onComplete });

  if (isLoading || !job) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Starting correlation...</span>
      </div>
    );
  }

  const pct = job.total > 0 ? Math.round((job.progress / job.total) * 100) : 0;

  return (
    <div className="space-y-2 rounded-lg border p-4">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          {job.status === "completed" ? (
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          ) : job.status === "failed" ? (
            <XCircle className="h-4 w-4 text-red-500" />
          ) : (
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
          )}
          <span className="font-medium capitalize">{job.status}</span>
        </div>
        <span className="text-muted-foreground">
          {job.progress}/{job.total} hosts
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full rounded-full bg-primary transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Stats */}
      <div className="flex gap-4 text-xs text-muted-foreground">
        <span>Matched: {job.matched}</span>
        <span>Review: {job.queued_for_review}</span>
        {job.errors.length > 0 && (
          <span className="text-red-500">Errors: {job.errors.length}</span>
        )}
      </div>

      {/* Error details */}
      {job.errors.length > 0 && (
        <ul className="mt-1 space-y-1 text-xs text-red-500">
          {job.errors.slice(0, 3).map((err, i) => (
            <li key={i}>{err}</li>
          ))}
          {job.errors.length > 3 && (
            <li>...and {job.errors.length - 3} more</li>
          )}
        </ul>
      )}
    </div>
  );
}
