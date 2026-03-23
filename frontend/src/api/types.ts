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
