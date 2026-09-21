import {
  Product,
  Keyword,
  ExistingContent,
  ResearchRun,
  Opportunity,
  ContentBrief,
  ContentDraft,
  PublishedContent,
  PublicArticle,
  DashboardStats,
  Store,
  ShopifyBlog,
  StoreStatusResponse,
  QualityAuditResult,
  PublishToShopifyResult
} from '../types';

const API_BASE = '';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const res = await fetch(url, { ...options, headers });
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  // Check 204 or empty response
  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return res.json();
  }
  return {} as T;
}

export const api = {
  // Dashboard
  getStats: () => request<DashboardStats>('/dashboard/stats'),

  // Products
  getProducts: () => request<Product[]>('/products'),
  getProduct: (id: number) => request<Product>(`/products/${id}`),
  createProduct: (data: { name: string; category: string; description: string }) =>
    request<Product>('/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id: number, data: Partial<{ name: string; category: string; description: string }>) =>
    request<Product>(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id: number) =>
    request<{ detail: string }>(`/products/${id}`, { method: 'DELETE' }),

  // Keywords
  getKeywords: () => request<Keyword[]>('/keywords'),
  createKeyword: (data: { keyword: string; search_volume: number }) =>
    request<Keyword>('/keywords', { method: 'POST', body: JSON.stringify(data) }),
  deleteKeyword: (id: number) =>
    request<{ detail: string }>(`/keywords/${id}`, { method: 'DELETE' }),

  // Existing Content
  getExistingContent: () => request<ExistingContent[]>('/content'),
  createExistingContent: (data: { title: string; url: string; primary_keyword?: string }) =>
    request<ExistingContent>('/existing-content', { method: 'POST', body: JSON.stringify(data) }),
  deleteExistingContent: (id: number) =>
    request<{ detail: string }>(`/existing-content/${id}`, { method: 'DELETE' }),

  // Research Runs
  getResearchRuns: () => request<ResearchRun[]>('/research-runs'),
  getResearchRun: (id: number) => request<ResearchRun>(`/research-runs/${id}`),
  createResearchRun: () => request<ResearchRun>('/research-runs', { method: 'POST' }),
  executeResearchRun: (id: number) =>
    request<{ id: number; status: string; completed_at: string; opportunities_count: number; opportunities: Opportunity[] }>(
      `/research-runs/${id}/execute`,
      { method: 'POST' }
    ),
  getRunOpportunities: (runId: number) =>
    request<Opportunity[]>(`/research-runs/${runId}/opportunities`),
  getRunActions: (runId: number) =>
    request<any[]>(`/research-runs/${runId}/actions`),
  getRunEvidence: (runId: number) =>
    request<any[]>(`/research-runs/${runId}/evidence`),

  // Competitors
  getCompetitors: () => request<any[]>('/competitors'),
  createCompetitor: (data: { domain: string; name?: string; category?: string; discovery_reason?: string }) =>
    request<any>('/competitors', { method: 'POST', body: JSON.stringify(data) }),
  getCompetitorPages: (competitorId: number) =>
    request<any[]>(`/competitors/${competitorId}/pages`),
  addCompetitorPage: (competitorId: number, data: { url: string; title?: string; content_summary?: string; page_type?: string }) =>
    request<any>(`/competitors/${competitorId}/pages`, { method: 'POST', body: JSON.stringify(data) }),

  // Opportunities
  getOpportunities: (status?: string) =>
    request<Opportunity[]>(`/opportunities${status ? `?status=${status}` : ''}`),
  approveOpportunity: (id: number) =>
    request<{ id: number; status: string }>(`/opportunities/${id}/approve`, { method: 'POST' }),
  rejectOpportunity: (id: number) =>
    request<{ id: number; status: string }>(`/opportunities/${id}/reject`, { method: 'POST' }),
  createBrief: (opportunityId: number) =>
    request<ContentBrief>(`/opportunities/${opportunityId}/create-brief`, { method: 'POST' }),

  // Briefs
  getBriefs: () => request<ContentBrief[]>('/content-briefs'),
  getBrief: (id: number) => request<ContentBrief>(`/content-briefs/${id}`),
  generateDraft: (briefId: number) =>
    request<ContentDraft>(`/briefs/${briefId}/generate-draft`, { method: 'POST' }),

  // Drafts
  getDrafts: () => request<ContentDraft[]>('/content-drafts'),
  getDraft: (id: number) => request<ContentDraft>(`/content-drafts/${id}`),
  updateDraft: (id: number, data: { title: string; introduction: string; body: string; conclusion: string }) =>
    request<ContentDraft>(`/content-drafts/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  approveDraft: (id: number) =>
    request<{ id: number; status: string }>(`/content-drafts/${id}/approve`, { method: 'POST' }),
  rejectDraft: (id: number) =>
    request<{ id: number; status: string }>(`/content-drafts/${id}/reject`, { method: 'POST' }),
  publishDraft: (draftId: number) =>
    request<PublishedContent>(`/content-drafts/${draftId}/publish`, { method: 'POST' }),

  // Publishing
  getPublishedContent: (status?: string) =>
    request<PublishedContent[]>(`/published-content${status ? `?status=${status}` : ''}`),
  unpublishContent: (id: number) =>
    request<PublishedContent>(`/published-content/${id}/unpublish`, { method: 'POST' }),
  getPublicArticle: (slug: string) =>
    request<PublicArticle>(`/blog/${slug}`),

  // Stores & Shopify Integration
  getStores: () => request<Store[]>('/stores'),
  createStore: (payload: { id: string; name: string; domain?: string; platform?: string }) =>
    request<Store>('/stores', { method: 'POST', body: JSON.stringify(payload) }),
  connectShopifyToken: (payload: { store_id: string; shop_domain: string; access_token: string; api_version?: string }) =>
    request<{ store_id: string; shop_domain: string; shop_name: string; status: string; installed_at: string; message: string }>(
      '/shopify/connect-token',
      { method: 'POST', body: JSON.stringify(payload) }
    ),
  triggerShopifySync: (storeId: string) =>
    request<{ store_id: string; status: string; blogs_synced: number; collections_synced: number; products_synced: number; articles_synced: number; total_items: number }>(
      `/shopify/sync/${storeId}`,
      { method: 'POST' }
    ),
  getStoreBlogs: (storeId: string) => request<ShopifyBlog[]>(`/shopify/blogs/${storeId}`),
  getStoreStatus: (storeId: string) => request<StoreStatusResponse>(`/shopify/status/${storeId}`),
  getDraftQualityCheck: (draftId: number, storeId: string = 'demo-store') =>
    request<QualityAuditResult>(`/content-drafts/${draftId}/quality-check?store_id=${storeId}`),
  publishDraftToShopify: (draftId: number, payload: { store_id: string; blog_id?: string }) =>
    request<PublishToShopifyResult>(`/content-drafts/${draftId}/publish-to-shopify`, { method: 'POST', body: JSON.stringify(payload) })
};
