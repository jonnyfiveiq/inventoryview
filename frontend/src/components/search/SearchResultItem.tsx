import { cn } from "@/lib/utils";
import type { Resource } from "@/api/types";

interface SearchResultItemProps {
  resource: Resource;
  isHighlighted?: boolean;
  onClick: () => void;
}

const stateColors: Record<string, string> = {
  running: "bg-green-500",
  connected: "bg-green-500",
  active: "bg-green-500",
  ready: "bg-green-500",
  powered_on: "bg-green-500",
  stopped: "bg-red-500",
  disconnected: "bg-red-500",
  terminated: "bg-red-500",
  powered_off: "bg-red-500",
};

export default function SearchResultItem({ resource, isHighlighted, onClick }: SearchResultItemProps) {
  const stateColor = stateColors[resource.state?.toLowerCase() ?? ""] ?? "bg-yellow-500";

  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center w-full px-3 py-2 text-left text-sm transition-colors rounded-md",
        isHighlighted
          ? "bg-accent/15 text-text"
          : "text-text-muted hover:bg-surface-hover hover:text-text"
      )}
      data-highlighted={isHighlighted}
    >
      <div className="flex-1 min-w-0">
        <div className="truncate font-medium text-text">{resource.name}</div>
        <div className="flex items-center gap-2 text-xs text-text-dim mt-0.5">
          <span className="px-1.5 py-0.5 rounded bg-surface-hover text-text-muted">
            {resource.vendor}
          </span>
          {resource.state && (
            <span className="flex items-center gap-1">
              <span className={cn("w-1.5 h-1.5 rounded-full", stateColor)} />
              {resource.state}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}
