export interface MarketplaceAccount {
  id: string;
  provider: string;
  external_user_id: string | null;
  username: string | null;
  display_name: string | null;
  email: string | null;
  avatar_url: string | null;
  profile_url: string | null;
  rating: number | null;
  reviews_count: number | null;
  projects_completed: number | null;
  verification_status: string | null;
  member_since: string | null;
  is_active: boolean;
  last_sync_at: string | null;
  sync_status: string;
  sync_error_message: string | null;
  connected_at: string | null;
  has_valid_token: boolean;
}

export interface MarketplaceAccountDetail extends MarketplaceAccount {
  email: string | null;
  disconnected_at: string | null;
  token_expires_at: string | null;
}

export interface MarketplaceConnectResponse {
  id: string;
  provider: string;
  external_user_id: string | null;
  username: string | null;
  display_name: string | null;
  avatar_url: string | null;
  message: string;
}

export interface MarketplaceSyncResponse {
  account_id: string;
  status: string;
  projects_found: number;
  projects_imported: number;
  projects_updated: number;
  projects_skipped: number;
  projects_failed: number;
  duration_ms: number | null;
}

export interface MarketplaceSyncHistoryItem {
  id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  projects_found: number;
  projects_imported: number;
  projects_updated: number;
  projects_skipped: number;
  projects_failed: number;
  error_message: string | null;
}

export interface MarketplaceProviderStats {
  provider: string;
  total_projects_imported: number;
  projects_viewed: number;
  proposals_generated: number;
  proposals_submitted: number;
  projects_won: number;
  projects_lost: number;
  win_rate: number;
  average_bid_amount: number;
  total_syncs: number;
  last_sync_at: string | null;
  last_sync_status: string | null;
}

export interface MarketplaceAuthUrlResponse {
  auth_url: string;
  state: string;
}
