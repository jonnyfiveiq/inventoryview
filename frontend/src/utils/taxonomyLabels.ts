const taxonomyLabels: Record<string, string> = {
  virtual_machine: "Virtual Machine",
  hypervisor: "Hypervisor",
  datastore: "Datastore",
  virtual_switch: "Virtual Switch",
  port_group: "Port Group",
  cluster: "Cluster",
  datacenter: "Datacenter",
  resource_pool: "Resource Pool",
  management_plane: "Management Plane",
  folder: "Folder",
  network: "Network",
  subnet: "Subnet",
  security_group: "Security Group",
  load_balancer: "Load Balancer",
  object_store: "Object Store",
  managed_database: "Managed Database",
  kubernetes_cluster: "Kubernetes Cluster",
  kubernetes_node: "Kubernetes Node",
  namespace: "Namespace",
  deployment: "Deployment",
  statefulset: "StatefulSet",
  ingress: "Ingress",
  service: "Service",
  persistent_volume: "Persistent Volume",
  route: "Route",
  virtual_network: "Virtual Network",
  network_gateway: "Network Gateway",
};

export function getTaxonomyLabel(type: string): string {
  return taxonomyLabels[type] || type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
