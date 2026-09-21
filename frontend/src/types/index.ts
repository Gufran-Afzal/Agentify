export interface Product {
  id: number;
  name: string;
  category: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Keyword {
  id: number;
  keyword: string;
  search_volume: number;
  created_at: string;
  updated_at: string;
  is_demo?: boolean;
}

export interface ExistingContent {
  id: number;
  title: string;
  url: string;
  primary_keyword?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResearchRun {
  id: number;
  status: 'created' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string | null;
}

export interface ResearchAction {
  id: number;
  research_run_id: number;
  action_type: string;
  arguments: Record<string, any>;
  result: Record<string, any>;
  status: string;
  created_at: string;
  completed_at?: string | null;
}

export interface ResearchEvidence {
  id: number;
  research_run_id?: number | null;
  store_id: string;
  source_type: string;
  source_reference: string;
  evidence_type: string;
  data: Record<string, any>;
  reliability: number;
  created_at: string;
  notes?: string;
}

export interface Competitor {
  id: number;
  store_id: string;
  domain: string;
  name: string;
  category: string;
  status: string;
  discovery_reason: string;
  created_at: string;
  updated_at: string;
}

export interface CompetitorPage {
  id: number;
  competitor_id: number;
  url: string;
  title: string;
  content_summary: string;
  page_type: string;
  created_at: string;
}

export interface Opportunity {
  id: number;
  research_run_id: number;
  title: string;
  reason: string;
  primary_keyword?: string | null;
  search_volume: number;
  confidence: 'high' | 'medium' | 'low';
  status: 'pending' | 'approved' | 'rejected';
  evidence: string[];
  created_at?: string | null;
  topic?: string;
  search_intent?: string;
  why_it_matters?: string;
  evidence_ids?: string[];
  supporting_evidence?: string[];
  missing_evidence?: string[];
  confidence_level?: 'strong' | 'moderate' | 'exploratory';
}

export interface ContentBrief {
  id: number;
  opportunity_id: number;
  title: string;
  objective: string;
  primary_keyword?: string | null;
  search_volume: number;
  search_intent: string;
  target_audience: string;
  suggested_sections: string[];
  suggested_angle: string;
  related_keywords: string[];
  opportunity_evidence: string[];
  status: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ContentDraft {
  id: number;
  brief_id: number;
  title: string;
  primary_keyword?: string | null;
  introduction: string;
  body: string;
  conclusion: string;
  status: 'draft' | 'approved' | 'rejected';
  created_at: string;
  updated_at?: string | null;
}

export interface PublishedContent {
  id: number;
  draft_id: number;
  title: string;
  slug: string;
  url: string;
  status: 'published' | 'unpublished';
  shopify_article_id?: string | null;
  shopify_blog_id?: string | null;
  shopify_status?: string | null;
  shopify_url?: string | null;
  published_at: string;
  created_at: string;
  updated_at: string;
}

export interface Store {
  id: string;
  name: string;
  domain: string;
  platform: string;
  created_at: string;
  updated_at: string;
}

export interface StoreConnection {
  status: string;
  shop_domain: string;
  last_synced_at?: string | null;
  sync_status: string;
  error_message?: string;
}

export interface StoreStatusResponse {
  store: Store;
  connection: StoreConnection | null;
  counts: {
    products: number;
    collections: number;
    existing_articles: number;
    blogs: number;
  };
}

export interface ShopifyBlog {
  id: number;
  store_id: string;
  shopify_blog_id: string;
  title: string;
  handle: string;
  commentable: string;
}

export interface QualityAuditCheck {
  name: string;
  category: string;
  passed: boolean;
  value?: string | null;
  message: string;
}

export interface QualityAuditResult {
  draft_id: number | null;
  score: number;
  grade: string;
  word_count: number;
  sentence_count: number;
  reading_ease: number;
  grade_level: number;
  checks: {
    name: string;
    category: string;
    passed: boolean;
    value?: string | null;
    message: string;
  }[];
  warnings: string[];
  matched_products: string[];
}

export interface PublishToShopifyResult {
  id: number;
  draft_id: number;
  title: string;
  slug: string;
  shopify_article_id: string;
  shopify_blog_id: string;
  shopify_status: string;
  shopify_url: string;
  admin_url: string;
  published_at: string;
  message: string;
}

export interface PublicArticle {
  title: string;
  slug: string;
  primary_keyword?: string | null;
  introduction: string;
  body: string;
  conclusion: string;
  published_at: string;
}

export interface DashboardStats {
  total_products: number;
  total_keywords: number;
  total_existing_content: number;
  research_runs: number;
  pending_opportunities: number;
  approved_opportunities: number;
  content_briefs: number;
  drafts: number;
  published_content: number;
}

export type NavView =
  | 'dashboard'
  | 'stores'
  | 'products'
  | 'keywords'
  | 'research'
  | 'opportunities'
  | 'competitors'
  | 'briefs'
  | 'drafts'
  | 'published'
  | 'public-blog';
