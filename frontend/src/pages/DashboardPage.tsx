import React from 'react';
import { DashboardStats, NavView } from '../types';
import {
  Package,
  Search,
  FlaskConical,
  Lightbulb,
  CheckCircle,
  FileText,
  FileEdit,
  Globe,
  ArrowRight,
  Sparkles
} from 'lucide-react';

interface DashboardPageProps {
  stats: DashboardStats | null;
  onNavigate: (view: NavView) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ stats, onNavigate }) => {
  return (
    <div>
      {/* Workflow Pipeline Bar */}
      <div className="card" style={{ padding: '18px 24px', marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="var(--primary)" />
            <span>Autonomous Content Operations Workflow</span>
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>End-to-end ecommerce intelligence</span>
        </div>

        <div className="pipeline-bar" style={{ margin: 0, padding: '12px 16px' }}>
          <div className="pipeline-step done">
            <Package size={14} /> Catalog
          </div>
          <span className="pipeline-arrow">→</span>
          <div className="pipeline-step active">
            <FlaskConical size={14} /> Research
          </div>
          <span className="pipeline-arrow">→</span>
          <div className="pipeline-step">
            <Lightbulb size={14} /> Opportunities
          </div>
          <span className="pipeline-arrow">→</span>
          <div className="pipeline-step">
            <CheckCircle size={14} /> Approval
          </div>
          <span className="pipeline-arrow">→</span>
          <div className="pipeline-step">
            <FileText size={14} /> Brief
          </div>
          <span className="pipeline-arrow">→</span>
          <div className="pipeline-step">
            <FileEdit size={14} /> Draft & Edit
          </div>
          <span className="pipeline-arrow">→</span>
          <div className="pipeline-step">
            <Globe size={14} /> Publishing
          </div>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="stats-grid">
        <div className="stat-card" onClick={() => onNavigate('products')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Products in Catalog</div>
          <div className="stat-value">{stats?.total_products ?? '—'}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Manage store catalog</span> <ArrowRight size={12} />
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate('keywords')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Search Keywords</div>
          <div className="stat-value">{stats?.total_keywords ?? '—'}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Track search demand</span> <ArrowRight size={12} />
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate('research')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Research Runs</div>
          <div className="stat-value" style={{ color: 'var(--accent-cyan)' }}>{stats?.research_runs ?? '—'}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Run intelligence scans</span> <ArrowRight size={12} />
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate('opportunities')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Pending Review</div>
          <div className="stat-value" style={{ color: 'var(--accent-amber)' }}>{stats?.pending_opportunities ?? '—'}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Approve/reject ideas</span> <ArrowRight size={12} />
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate('briefs')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Content Briefs</div>
          <div className="stat-value">{stats?.content_briefs ?? '—'}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Generate drafts</span> <ArrowRight size={12} />
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate('drafts')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Active Drafts</div>
          <div className="stat-value" style={{ color: 'var(--accent-purple)' }}>{stats?.drafts ?? '—'}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>Edit and approve</span> <ArrowRight size={12} />
          </div>
        </div>

        <div className="stat-card" onClick={() => onNavigate('published')} style={{ cursor: 'pointer' }}>
          <div className="stat-label">Live Publications</div>
          <div className="stat-value" style={{ color: 'var(--accent-emerald)' }}>{stats?.published_content ?? '—'}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>View public articles</span> <ArrowRight size={12} />
          </div>
        </div>
      </div>

      {/* Fast Action Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">1. Content Discovery</div>
              <div className="card-subtitle">Scan search demand and match with products</div>
            </div>
          </div>
          <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', marginBottom: '18px' }}>
            The research engine analyzes product attributes, correlates search volumes, and detects topic gaps while automatically preventing duplicate content.
          </p>
          <button className="btn btn-primary" onClick={() => onNavigate('research')}>
            <FlaskConical size={16} /> Run Research Scan
          </button>
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">2. Human Editorial Control</div>
              <div className="card-subtitle">Review, edit, and approve before publishing</div>
            </div>
          </div>
          <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', marginBottom: '18px' }}>
            Every generated brief and draft requires human sign-off. Editors can refine titles, introductions, body copy, and conclusions prior to publication.
          </p>
          <button className="btn btn-secondary" onClick={() => onNavigate('drafts')}>
            <FileEdit size={16} /> Open Content Editor
          </button>
        </div>
      </div>
    </div>
  );
};
