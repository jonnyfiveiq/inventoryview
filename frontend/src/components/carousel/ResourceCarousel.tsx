import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import ResourceCard from "./ResourceCard";
import type { Resource } from "@/api/types";

const typeLabels: Record<string, string> = {
  virtual_machine: "Virtual Machines",
  hypervisor: "Hypervisors",
  datastore: "Datastores",
  cluster: "Clusters",
  virtual_switch: "Virtual Switches",
  port_group: "Port Groups",
  datacenter: "Datacenters",
  management_plane: "Management Planes",
  resource_pool: "Resource Pools",
  subnet: "Subnets",
  load_balancer: "Load Balancers",
  security_group: "Security Groups",
  container: "Containers",
  pod: "Pods",
  namespace: "Namespaces",
  node: "Nodes",
};

interface ResourceCarouselProps {
  type: string;
  resources: Resource[];
}

export default function ResourceCarousel({ type, resources }: ResourceCarouselProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const amount = 280; // card width + gap
    scrollRef.current.scrollBy({
      left: direction === "left" ? -amount : amount,
      behavior: "smooth",
    });
  };

  const label = typeLabels[type] || type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h2 className="text-base font-semibold text-text">{label}</h2>
          <span className="text-xs text-text-dim bg-surface-hover rounded-full px-2 py-0.5">
            {resources.length}
          </span>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => scroll("left")}
            className="p-1.5 rounded-md text-text-muted hover:text-text hover:bg-surface-hover transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => scroll("right")}
            className="p-1.5 rounded-md text-text-muted hover:text-text hover:bg-surface-hover transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-2"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {resources.map((resource) => (
          <div key={resource.uid} className="snap-start">
            <ResourceCard
              resource={resource}
              onVendorClick={(vendor) => navigate(`/providers/${vendor}`)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
