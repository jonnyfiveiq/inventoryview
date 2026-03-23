import { Activity } from "lucide-react";

interface AutomationBadgeProps {
  totalJobs: number;
  lastAutomated?: string | null;
  className?: string;
}

export default function AutomationBadge({ totalJobs, lastAutomated, className = "" }: AutomationBadgeProps) {
  if (totalJobs === 0) return null;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-accent/10 text-accent rounded ${className}`}
      title={lastAutomated ? `Last automated: ${new Date(lastAutomated).toLocaleDateString()}` : undefined}
    >
      <Activity className="w-3 h-3" />
      {totalJobs} job{totalJobs !== 1 ? "s" : ""}
    </span>
  );
}
