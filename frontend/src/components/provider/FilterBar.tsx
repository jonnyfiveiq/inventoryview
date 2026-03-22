import { X } from "lucide-react";
import type { Resource } from "@/api/types";

export interface Filters {
  category?: string;
  state?: string;
  region?: string;
  normalised_type?: string;
  [key: string]: string | undefined;
}

interface FilterBarProps {
  filters: Filters;
  onFilterChange: (filters: Filters) => void;
  resources: Resource[];
}

export default function FilterBar({ filters, onFilterChange, resources }: FilterBarProps) {
  const unique = (key: keyof Resource) =>
    [...new Set(resources.map((r) => r[key]).filter(Boolean) as string[])].sort();

  const categories = unique("category");
  const states = unique("state");
  const regions = unique("region");
  const types = unique("normalised_type");

  const hasFilters = Object.values(filters).some(Boolean);

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <FilterSelect
        label="Category"
        value={filters.category}
        options={categories}
        onChange={(v) => onFilterChange({ ...filters, category: v })}
      />
      <FilterSelect
        label="State"
        value={filters.state}
        options={states}
        onChange={(v) => onFilterChange({ ...filters, state: v })}
      />
      <FilterSelect
        label="Region"
        value={filters.region}
        options={regions}
        onChange={(v) => onFilterChange({ ...filters, region: v })}
      />
      <FilterSelect
        label="Type"
        value={filters.normalised_type}
        options={types}
        onChange={(v) => onFilterChange({ ...filters, normalised_type: v })}
      />
      {hasFilters && (
        <button
          onClick={() => onFilterChange({})}
          className="flex items-center gap-1 text-sm text-text-muted hover:text-text transition-colors"
        >
          <X className="w-3.5 h-3.5" />
          Clear
        </button>
      )}
    </div>
  );
}

function FilterSelect({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value?: string;
  options: string[];
  onChange: (value?: string) => void;
}) {
  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value || undefined)}
      className="bg-surface border border-border rounded-md px-3 py-1.5 text-sm text-text focus:outline-none focus:border-accent transition-colors"
    >
      <option value="">All {label}s</option>
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  );
}
