export interface Resource {
  uid: string;
  name: string;
  vendor_id: string;
  vendor: string;
  vendor_type: string;
  normalised_type: string;
  category: string;
  region: string | null;
  state: string | null;
  classification_confidence: number | null;
  classification_method: string | null;
  first_seen: string;
  last_seen: string;
  raw_properties: Record<string, unknown> | null;
}

export interface Relationship {
  source_uid: string;
  target_uid: string;
  type: string;
  confidence: number;
  source_collector: string | null;
  established_at: string;
  last_confirmed: string;
  inference_method: string | null;
  metadata: Record<string, unknown> | null;
}

export interface SubgraphNode {
  uid: string;
  name: string;
  category: string;
  vendor: string;
  normalised_type: string;
}

export interface SubgraphEdge {
  source_uid: string;
  target_uid: string;
  type: string;
  confidence: number;
}

export interface SubgraphResponse {
  nodes: SubgraphNode[];
  edges: SubgraphEdge[];
}

export interface PaginatedResponse<T> {
  data: T[];
  next_cursor: string | null;
  page_size: number;
}

export interface AuthSession {
  token: string;
  token_type: string;
  expires_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface SetupStatus {
  setup_complete: boolean;
}

export interface SetupInitResponse {
  message: string;
  username: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  database: string;
  timestamp: string;
}

export interface DriftEntry {
  id: string;
  resource_uid: string;
  field: string;
  old_value: string | null;
  new_value: string | null;
  changed_at: string;
  source: string;
}

export interface DriftResponse {
  data: DriftEntry[];
}

export interface DriftExistsResponse {
  has_drift: boolean;
}

export interface DriftTimelineDay {
  date: string;
  count: number;
  fields: string[];
}

export interface DriftTimelineResponse {
  data: DriftTimelineDay[];
  total_drift_count: number;
  first_seen: string;
}

export interface FleetDriftTimelineResponse {
  data: DriftTimelineDay[];
  fleet_avg_lifetime: number;
  total_resources_with_drift: number;
}

export interface AssetTwin {
  uid: string;
  name: string;
  vendor: string;
  normalised_type: string;
  category: string;
  matched_key: string;
  matched_value: string;
  confidence: number;
}

export interface AssetTwinsResponse {
  data: AssetTwin[];
}

export interface AssetChainNode {
  uid: string;
  name: string;
  vendor: string;
  normalised_type: string;
  category: string;
  vendor_type: string;
  state: string;
}

export interface AssetChainEdge {
  source_uid: string;
  target_uid: string;
  matched_key: string;
  matched_value: string;
}

export interface AssetChainResponse {
  nodes: AssetChainNode[];
  edges: AssetChainEdge[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}

export interface Playlist {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface PlaylistDetailResponse {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
  resources: PlaylistResourceSummary[];
}

export interface PlaylistResourceSummary {
  uid: string;
  name: string;
  vendor: string;
  normalised_type: string;
  category: string;
  state: string | null;
}

export interface PlaylistResourceFull extends PlaylistResourceSummary {
  vendor_id: string;
  vendor_type: string;
  region: string | null;
  first_seen: string;
  last_seen: string;
  classification_confidence: number | null;
  classification_method: string | null;
  raw_properties: Record<string, unknown> | null;
}

export interface PlaylistMembership {
  playlist_id: string;
  resource_uid: string;
  added_at: string;
}

export interface PlaylistActivity {
  id: string;
  action: string;
  resource_uid: string | null;
  resource_name: string | null;
  resource_vendor: string | null;
  detail: string | null;
  occurred_at: string;
}

export interface PlaylistActivityTimelineDay {
  date: string;
  count: number;
  actions: string[];
}

export interface PlaylistActivityTimelineResponse {
  data: PlaylistActivityTimelineDay[];
  total_activity_count: number;
}

// --- AAP Automation Correlation ---

export interface AAPHostItem {
  id: string;
  host_id: string;
  hostname: string;
  smbios_uuid: string | null;
  org_id: string;
  inventory_id: string;
  first_seen: string;
  last_seen: string;
  total_jobs: number;
  total_events: number;
  correlation_type: string;
  correlation_status: string;
  match_score: number | null;
  match_reason: string | null;
  correlated_resource: {
    uid: string;
    name: string;
    vendor: string;
    normalised_type: string;
  } | null;
}

export interface AAPHostListResponse {
  items: AAPHostItem[];
  next_cursor: string | null;
  total_count: number;
}

export interface UploadCorrelationSummary {
  auto_matched: number;
  pending_review: number;
  unmatched: number;
}

export interface UploadResponse {
  import_id: string;
  source_label: string;
  hosts_imported: number;
  hosts_updated: number;
  jobs_imported: number;
  events_counted: number;
  indirect_nodes_imported: number;
  correlation_summary: UploadCorrelationSummary | null;
}

export interface PendingMatchItem {
  id: string;
  aap_host: {
    id: string;
    host_id: string;
    hostname: string;
    smbios_uuid: string | null;
    total_jobs: number;
  };
  suggested_resource: {
    uid: string;
    name: string;
    vendor: string;
    normalised_type: string;
  } | null;
  match_score: number;
  match_reason: string;
  status: string;
  created_at: string;
}

export interface PendingMatchListResponse {
  items: PendingMatchItem[];
  next_cursor: string | null;
  total_count: number;
}

export interface ReviewAction {
  pending_match_id: string;
  action: "approve" | "reject" | "ignore";
  override_resource_uid?: string | null;
}

export interface ReviewResponse {
  processed: number;
  results: {
    pending_match_id: string;
    action: string;
    success: boolean;
    learned_mapping_created: boolean;
    error?: string | null;
  }[];
}

export interface ProviderCoverage {
  vendor: string;
  total: number;
  automated: number;
  coverage_percentage: number;
}

export interface CoverageResponse {
  total_resources: number;
  automated_resources: number;
  coverage_percentage: number;
  by_provider: ProviderCoverage[];
  top_automated: {
    resource_uid: string;
    resource_name: string;
    vendor: string;
    total_jobs: number;
    last_automated: string;
  }[];
  recent_imports: {
    source_label: string;
    imported_at: string;
    hosts_count: number;
  }[];
}

export interface JobExecutionItem {
  job_id: string;
  job_name: string;
  ok: number;
  changed: number;
  failures: number;
  dark: number;
  skipped: number;
  project: string | null;
  org_name: string | null;
  correlation_type: string;
  executed_at: string;
}

export interface HistoryResponse {
  resource_uid: string;
  first_automated: string | null;
  last_automated: string | null;
  total_jobs: number;
  aap_hosts: {
    hostname: string;
    correlation_type: string;
    match_reason: string | null;
  }[];
  executions: {
    items: JobExecutionItem[];
    next_cursor: string | null;
    total_count: number;
  };
}

export interface AutomationGraphNode {
  id: string;
  label: string;
  type: string;
  vendor?: string | null;
  normalised_type?: string | null;
  correlation_type?: string | null;
  total_jobs?: number | null;
}

export interface AutomationGraphEdge {
  source: string;
  target: string;
  type: string;
  confidence?: number | null;
  correlation_type?: string | null;
  inference_method?: string | null;
}

export interface AutomationGraphResponse {
  nodes: AutomationGraphNode[];
  edges: AutomationGraphEdge[];
}
