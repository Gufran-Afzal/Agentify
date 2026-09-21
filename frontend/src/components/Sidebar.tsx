import React from 'react';
import {
  LayoutDashboard,
  Package,
  Search,
  FlaskConical,
  Lightbulb,
  FileText,
  FileEdit,
  Globe,
  BookOpen
} from 'lucide-react';
import { NavView, DashboardStats } from '../types';

interface SidebarProps {
  currentView: NavView;
  onNavigate: (view: NavView) => void;
  stats: DashboardStats | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onNavigate, stats }) => {
  const navItems: { id: NavView; label: string; icon: React.ReactNode; count?: number }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={18} /> },
    { id: 'products', label: 'Products', icon: <Package size={18} />, count: stats?.total_products },
    { id: 'keywords', label: 'Keywords', icon: <Search size={18} />, count: stats?.total_keywords },
    { id: 'research', label: 'Research', icon: <FlaskConical size={18} />, count: stats?.research_runs },
    { id: 'opportunities', label: 'Opportunities', icon: <Lightbulb size={18} />, count: stats?.pending_opportunities },
    { id: 'briefs', label: 'Briefs', icon: <FileText size={18} />, count: stats?.content_briefs },
    { id: 'drafts', label: 'Drafts', icon: <FileEdit size={18} />, count: stats?.drafts },
    { id: 'published', label: 'Published Content', icon: <Globe size={18} />, count: stats?.published_content },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-badge">A</div>
        <div>
          <div className="brand-title">Adaptive Content</div>
          <div className="brand-subtitle">Intelligence Ops</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >
              <span style={{ color: isActive ? 'var(--primary)' : 'inherit', display: 'flex' }}>
                {item.icon}
              </span>
              <span>{item.label}</span>
              {item.count !== undefined && item.count > 0 && (
                <span className="nav-counter">{item.count}</span>
              )}
            </button>
          );
        })}

        {currentView === 'public-blog' && (
          <button
            className="nav-item active"
            style={{ marginTop: '12px', borderLeftColor: 'var(--accent-cyan)' }}
            onClick={() => onNavigate('public-blog')}
          >
            <span style={{ color: 'var(--accent-cyan)', display: 'flex' }}>
              <BookOpen size={18} />
            </span>
            <span>Public Article</span>
          </button>
        )}
      </nav>

      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-subtle)', fontSize: '11.5px', color: 'var(--text-dim)' }}>
        <div>Catalog: <strong>Skincare Store</strong></div>
        <div style={{ marginTop: '4px' }}>Status: <span style={{ color: 'var(--accent-emerald)' }}>● Operational</span></div>
      </div>
    </aside>
  );
};
