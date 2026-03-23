import { Link } from "react-router-dom";
import { Plus, Minus, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { usePlaylistActivity } from "@/hooks/usePlaylists";
import { cn } from "@/lib/utils";

interface PlaylistActivityLogProps {
  identifier: string;
  filterDate?: string;
  onClearFilter?: () => void;
}

const ACTION_CONFIG: Record<string, { icon: typeof Plus; color: string; label: string }> = {
  resource_added: { icon: Plus, color: "text-green-500", label: "Added" },
  resource_removed: { icon: Minus, color: "text-red-500", label: "Removed" },
  resource_removed_by_deletion: { icon: Trash2, color: "text-amber-500", label: "Deleted" },
  playlist_created: { icon: Plus, color: "text-accent", label: "Created" },
  playlist_renamed: { icon: Plus, color: "text-accent", label: "Renamed" },
  playlist_deleted: { icon: Trash2, color: "text-red-500", label: "Deleted" },
};

export default function PlaylistActivityLog({
  identifier,
  filterDate,
  onClearFilter,
}: PlaylistActivityLogProps) {
  const { data, isLoading } = usePlaylistActivity(identifier, {
    date: filterDate,
    page_size: 50,
  });

  const activities = data?.data ?? [];

  if (isLoading) {
    return <div className="h-32 bg-surface rounded-lg animate-pulse" />;
  }

  return (
    <div>
      {filterDate && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-text-muted">
            Filtered to: <span className="font-medium text-text">{filterDate}</span>
          </span>
          <button
            onClick={onClearFilter}
            className="text-xs text-accent hover:text-accent-hover"
          >
            Clear
          </button>
        </div>
      )}

      {activities.length === 0 ? (
        <div className="text-center py-8 text-text-dim text-sm">
          {filterDate ? "No activity on this date." : "No activity yet."}
        </div>
      ) : (
        <div className="space-y-1">
          {activities.map((entry, i) => {
            const config = ACTION_CONFIG[entry.action] ?? {
              icon: Plus,
              color: "text-text-dim",
              label: entry.action,
            };
            const Icon = config.icon;
            const time = new Date(entry.occurred_at).toLocaleString();

            return (
              <div
                key={i}
                className="flex items-start gap-3 px-3 py-2 rounded hover:bg-surface-hover transition-colors"
              >
                <Icon className={cn("w-4 h-4 mt-0.5 shrink-0", config.color)} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm">
                    <span className={cn("font-medium", config.color)}>{config.label}</span>
                    {entry.resource_name && (
                      <>
                        {" "}
                        {entry.resource_uid ? (
                          <Link
                            to={`/resources/${entry.resource_uid}`}
                            className="text-accent hover:text-accent-hover"
                          >
                            {entry.resource_name}
                          </Link>
                        ) : (
                          <span className="text-text-muted">{entry.resource_name}</span>
                        )}
                      </>
                    )}
                    {entry.resource_vendor && (
                      <span className="text-text-dim text-xs ml-1">({entry.resource_vendor})</span>
                    )}
                  </div>
                  {entry.detail && (
                    <p className="text-xs text-text-dim mt-0.5">{entry.detail}</p>
                  )}
                </div>
                <span className="text-[10px] text-text-dim whitespace-nowrap shrink-0">
                  {time}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {data?.next_cursor && (
        <div className="flex justify-center mt-3">
          <span className="text-xs text-text-dim">
            More activity entries available
          </span>
        </div>
      )}
    </div>
  );
}
