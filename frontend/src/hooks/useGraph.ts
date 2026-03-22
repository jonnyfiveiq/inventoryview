import { useQuery } from "@tanstack/react-query";
import { getResourceGraph } from "@/api/resources";

export function useGraph(uid: string | null, depth: number = 1) {
  return useQuery({
    queryKey: ["graph", uid, depth],
    queryFn: () => getResourceGraph(uid!, depth),
    enabled: !!uid,
  });
}
