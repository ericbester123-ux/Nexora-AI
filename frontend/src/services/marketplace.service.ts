import { api } from "@/lib/api";
import type {
  MarketplaceAccount,
  MarketplaceAccountDetail,
  MarketplaceConnectResponse,
  MarketplaceSyncResponse,
  MarketplaceSyncHistoryItem,
  MarketplaceProviderStats,
  MarketplaceAuthUrlResponse,
} from "@/types/marketplace";

const BASE = "/marketplace";

export const marketplaceService = {
  async getAccounts(): Promise<MarketplaceAccount[]> {
    const res = await api.get(`${BASE}/accounts`);
    return res.data;
  },

  async getAccount(accountId: string): Promise<MarketplaceAccountDetail> {
    const res = await api.get(`${BASE}/accounts/${accountId}`);
    return res.data;
  },

  async linkByEmail(provider: string, email: string): Promise<MarketplaceConnectResponse> {
    const res = await api.post(`${BASE}/${provider}/email-link`, { email });
    return res.data;
  },

  async getAuthUrl(provider: string): Promise<MarketplaceAuthUrlResponse> {
    const res = await api.get(`${BASE}/${provider}/auth-url`);
    return res.data;
  },

  async exchangeCode(
    provider: string,
    code: string,
    state: string,
    redirectUri?: string
  ): Promise<MarketplaceConnectResponse> {
    const res = await api.post(`${BASE}/${provider}/exchange-code`, {
      code,
      state,
      redirect_uri: redirectUri,
    });
    return res.data;
  },

  async directConnect(
    provider: string,
    oauthToken: string,
    refreshToken?: string,
    expiresIn?: number
  ): Promise<MarketplaceConnectResponse> {
    const res = await api.post(`${BASE}/${provider}/direct-connect`, {
      oauth_token: oauthToken,
      refresh_token: refreshToken,
      expires_in: expiresIn,
    });
    return res.data;
  },

  async disconnect(accountId: string): Promise<{ message: string }> {
    const res = await api.delete(`${BASE}/accounts/${accountId}`);
    return res.data;
  },

  async reconnect(accountId: string): Promise<{ message: string }> {
    const res = await api.post(`${BASE}/accounts/${accountId}/reconnect`);
    return res.data;
  },

  async sync(
    accountId: string,
    maxResults: number = 50
  ): Promise<MarketplaceSyncResponse> {
    const res = await api.post(
      `${BASE}/accounts/${accountId}/sync?max_results=${maxResults}`
    );
    return res.data;
  },

  async getSyncHistory(
    accountId: string,
    limit: number = 20
  ): Promise<MarketplaceSyncHistoryItem[]> {
    const res = await api.get(
      `${BASE}/accounts/${accountId}/sync-history?limit=${limit}`
    );
    return res.data;
  },

  async getSyncStatus(): Promise<
    { account_id: string; provider: string; sync_status: string; last_sync_at: string | null; sync_error_message: string | null }[]
  > {
    const res = await api.get(`${BASE}/sync-status`);
    return res.data;
  },

  async getStats(accountId: string): Promise<MarketplaceProviderStats> {
    const res = await api.get(`${BASE}/accounts/${accountId}/stats`);
    return res.data;
  },
};
