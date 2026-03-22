import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import type { Resource } from "@/api/types";

const vendorColors: Record<string, string> = {
  vmware: "bg-vendor-vmware/20 text-vendor-vmware border-vendor-vmware/30",
  aws: "bg-vendor-aws/20 text-vendor-aws border-vendor-aws/30",
  azure: "bg-vendor-azure/20 text-vendor-azure border-vendor-azure/30",
  openshift: "bg-vendor-openshift/20 text-vendor-openshift border-vendor-openshift/30",
};

const stateColors: Record<string, string> = {
  poweredOn: "bg-state-on",
  running: "bg-state-on",
  connected: "bg-state-connected",
  poweredOff: "bg-state-off",
  stopped: "bg-state-off",
  disconnected: "bg-state-disconnected",
  maintenance: "bg-state-maintenance",
  decommissioned: "bg-state-off",
  template: "bg-text-dim",
};

interface ResourceCardProps {
  resource: Resource;
  onVendorClick?: (vendor: string) => void;
}

export default function ResourceCard({ resource, onVendorClick }: ResourceCardProps) {
  const navigate = useNavigate();

  const vendorClass = vendorColors[resource.vendor] || "bg-text-dim/20 text-text-muted border-text-dim/30";
  const stateColor = stateColors[resource.state ?? ""] || "bg-text-dim";

  return (
    <div
      onClick={() => navigate(`/resources/${resource.uid}`)}
      className="flex-shrink-0 w-64 bg-surface border border-border rounded-lg p-4 cursor-pointer hover:border-border-light hover:bg-surface-hover transition-colors"
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-medium text-text truncate flex-1 mr-2">
          {resource.name}
        </h3>
        <div className={cn("flex items-center gap-1.5")}>
          <span className={cn("w-2 h-2 rounded-full", stateColor)} />
          <span className="text-xs text-text-muted">{resource.state ?? "unknown"}</span>
        </div>
      </div>

      <button
        onClick={(e) => {
          e.stopPropagation();
          onVendorClick?.(resource.vendor);
        }}
        className={cn(
          "inline-block text-xs font-medium px-2 py-0.5 rounded border mb-2 hover:opacity-80 transition-opacity",
          vendorClass
        )}
      >
        {resource.vendor}
      </button>

      <div className="text-xs text-text-dim space-y-0.5">
        <div>{resource.vendor_type}</div>
        <div className="text-text-muted">{resource.category}</div>
      </div>
    </div>
  );
}
