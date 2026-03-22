import { Link } from "react-router-dom";
import type { Resource } from "@/api/types";

interface VendorInfo {
  name: string;
  count: number;
  types: number;
  color: string;
  borderColor: string;
}

const vendorStyles: Record<string, { color: string; borderColor: string }> = {
  vmware: { color: "#60a5fa", borderColor: "#60a5fa" },
  aws: { color: "#f59e0b", borderColor: "#f59e0b" },
  azure: { color: "#06b6d4", borderColor: "#06b6d4" },
  openshift: { color: "#ef4444", borderColor: "#ef4444" },
};

interface VendorCarouselProps {
  resources: Resource[];
}

export default function VendorCarousel({ resources }: VendorCarouselProps) {
  const vendors: VendorInfo[] = [];
  const vendorMap: Record<string, { count: number; types: Set<string> }> = {};

  for (const r of resources) {
    if (!vendorMap[r.vendor]) {
      vendorMap[r.vendor] = { count: 0, types: new Set() };
    }
    vendorMap[r.vendor].count++;
    vendorMap[r.vendor].types.add(r.normalised_type);
  }

  for (const [name, data] of Object.entries(vendorMap)) {
    const style = vendorStyles[name.toLowerCase()] || { color: "#6366f1", borderColor: "#6366f1" };
    vendors.push({
      name,
      count: data.count,
      types: data.types.size,
      ...style,
    });
  }

  vendors.sort((a, b) => b.count - a.count);

  return (
    <div className="mb-6">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3">
        Providers
      </h2>
      <div className="flex gap-3 overflow-x-auto pb-2" style={{ scrollbarWidth: "none" }}>
        {vendors.map((v) => (
          <Link
            key={v.name}
            to={`/vendors/${v.name}`}
            className="flex-shrink-0 w-48 bg-surface border rounded-lg p-4 hover:bg-surface-hover transition-colors group"
            style={{ borderColor: v.borderColor + "44" }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: v.color }}
              />
              <span
                className="text-sm font-semibold capitalize group-hover:underline"
                style={{ color: v.color }}
              >
                {v.name}
              </span>
            </div>
            <div className="text-xs text-text-muted space-y-0.5">
              <div>
                <span className="text-text font-medium">{v.count}</span> resources
              </div>
              <div>
                <span className="text-text font-medium">{v.types}</span> resource types
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
