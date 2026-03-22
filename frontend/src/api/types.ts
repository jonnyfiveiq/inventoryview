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

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}
