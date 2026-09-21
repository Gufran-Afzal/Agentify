import React from 'react';
import { NavView } from '../types';
import { Sparkles, RefreshCw } from 'lucide-react';

interface HeaderProps {
  currentView: NavView;
  onRefresh: () => void;
  loading: boolean;
}

const titles: Record<NavView, { title: string; subtitle: string }> = {
  dashboard: { title: 'Operations Dashboard', subtitle: 'Real-time overview of content demand, pipeline stages, and publications' },
  products: { title: 'Product Catalog', subtitle: 'Active store merchandise analyzed for keyword demand and topic coverage' },
  keywords: { title: 'Search Demand Intelligence', subtitle: 'Target keywords with tracked search volumes and consumer intent' },
  research: { title: 'Research & Opportunity Engine', subtitle: 'Automated research runs analyzing catalogs against search volume signals' },
  opportunities: { title: 'Content Opportunities', subtitle: 'Ranked, evidence-backed article opportunities awaiting human editorial review' },
  briefs: { title: 'Content Briefs', subtitle: 'Structured blueprints detailing search intent, target audience, and required sections' },
  drafts: { title: 'Content Drafts & Editor', subtitle: 'Draft production, in-place human editing, and approval pipeline' },
  published: { title: 'Published Articles', subtitle: 'Live customer-facing content with SEO slugs and public article views' },
  'public-blog': { title: 'Public Blog Reader', subtitle: 'Live customer article view rendered directly from published content' }
};

export const Header: React.FC<HeaderProps> = ({ currentView, onRefresh, loading }) => {
  const current = titles[currentView] || { title: 'Content Intelligence', subtitle: '' };

  return (
    <header className="top-bar">
      <div>
        <div className="top-bar-title">
          {current.title}
        </div>
        <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '2px' }}>
          {current.subtitle}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          className="btn btn-secondary btn-sm"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh view data"
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--accent-cyan)' }}>
          <Sparkles size={14} />
          <span>AI Assisted Pipeline</span>
        </div>
      </div>
    </header>
  );
};
