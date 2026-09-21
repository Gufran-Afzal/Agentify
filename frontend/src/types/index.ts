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
  published_at: string;
  created_at: string;
  updated_at: string;
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
  | 'products'
  | 'keywords'
  | 'research'
  | 'opportunities'
  | 'briefs'
  | 'drafts'
  | 'published'
  | 'public-blog';
