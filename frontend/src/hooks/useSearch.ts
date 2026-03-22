import { useQuery } from "@tanstack/react-query";
import { listResources } from "@/api/resources";

export function useSearch(query: string) {
  return useQuery({
    queryKey: ["resources", "search", query],
    queryFn: () => listResources({ search: query, page_size: 50 }),
    enabled: query.length >= 2,
    staleTime: 30 * 1000,
  });
}
