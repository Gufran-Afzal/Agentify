import React, { useState, useEffect } from 'react';
import { Competitor, CompetitorPage as CompetitorPageType } from '../types';
import { api } from '../api/client';
import { Globe, Plus, ExternalLink, ChevronDown, ChevronRight, FileText } from 'lucide-react';

export const CompetitorsPage: React.FC = () => {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [selectedCompetitorId, setSelectedCompetitorId] = useState<number | null>(null);
  const [pages, setPages] = useState<CompetitorPageType[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // New competitor form
  const [showAddModal, setShowAddModal] = useState(false);
  const [domain, setDomain] = useState('');
  const [name, setName] = useState('');
  const [category, setCategory] = useState('content_competitor');
  const [discoveryReason, setDiscoveryReason] = useState('');

  // New page form
  const [pageUrl, setPageUrl] = useState('');
  const [pageTitle, setPageTitle] = useState('');
  const [pageSummary, setPageSummary] = useState('');

  const loadCompetitors = async () => {
    try {
      setLoading(true);
      const data = await api.getCompetitors();
      setCompetitors(data);
      if (data.length > 0 && selectedCompetitorId === null) {
        setSelectedCompetitorId(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load competitors');
    } finally {
      setLoading(false);
    }
  };

  const loadPages = async (compId: number) => {
    try {
      const data = await api.getCompetitorPages(compId);
      setPages(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load competitor pages');
    }
  };

  useEffect(() => {
    loadCompetitors();
  }, []);

  useEffect(() => {
    if (selectedCompetitorId !== null) {
      loadPages(selectedCompetitorId);
    }
  }, [selectedCompetitorId]);

  const handleAddCompetitor = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain.trim()) return;
    try {
      setError(null);
      await api.createCompetitor({
        domain: domain.trim(),
        name: name.trim() || domain.trim(),
        category,
        discovery_reason: discoveryReason.trim(),
      });
      setSuccess(`Competitor '${domain}' added successfully!`);
      setDomain('');
      setName('');
      setDiscoveryReason('');
      setShowAddModal(false);
      loadCompetitors();
    } catch (err: any) {
      setError(err.message || 'Failed to add competitor');
    }
  };

  const handleAddPage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompetitorId || !pageUrl.trim()) return;
    try {
      setError(null);
      await api.addCompetitorPage(selectedCompetitorId, {
        url: pageUrl.trim(),
        title: pageTitle.trim(),
        content_summary: pageSummary.trim(),
        page_type: 'blog',
      });
      setSuccess('Page added for competitor analysis!');
      setPageUrl('');
      setPageTitle('');
      setPageSummary('');
      loadPages(selectedCompetitorId);
    } catch (err: any) {
      setError(err.message || 'Failed to add competitor page');
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px', marginBottom: '24px' }}>
        <div>
          <div className="card-title" style={{ fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Globe size={20} color="var(--primary)" />
            <span>Competitor Intelligence & Content Analysis</span>
          </div>
          <div className="card-subtitle">
            Track domain competitors, analyze their published ranking pages, and extract topic gaps.
          </div>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowAddModal(true)}
          style={{ padding: '9px 18px', fontSize: '13px' }}
        >
          <Plus size={16} /> Add Competitor
        </button>
      </div>

      {error && <div className="alert-banner alert-error">{error}</div>}
      {success && <div className="alert-banner alert-success">{success}</div>}

      {/* Add Competitor Modal / Form */}
      {showAddModal && (
        <div className="card" style={{ marginBottom: '24px', padding: '20px', border: '1px solid var(--primary)' }}>
          <div className="card-title" style={{ fontSize: '15px', marginBottom: '14px' }}>Track New Competitor Domain</div>
          <form onSubmit={handleAddCompetitor} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>Domain *</label>
              <input
                type="text"
                className="input"
                placeholder="e.g. glowskincare.com"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                required
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>Brand / Store Name</label>
              <input
                type="text"
                className="input"
                placeholder="e.g. Glow Skincare"
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>Category</label>
              <select
                className="input"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                style={{ width: '100%' }}
              >
                <option value="content_competitor">Content Competitor (SEO)</option>
                <option value="business_competitor">Direct Ecommerce Competitor</option>
                <option value="search_competitor">Search Query Competitor</option>
              </select>
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>Discovery Reason</label>
              <input
                type="text"
                className="input"
                placeholder="e.g. Outranking us for 'vitamin c serum guide'"
                value={discoveryReason}
                onChange={(e) => setDiscoveryReason(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
            <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowAddModal(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary btn-sm">
                Save Competitor
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Main Grid: Competitor List + Analyzed Pages */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
        {/* Competitors List */}
        <div className="card" style={{ padding: '20px' }}>
          <div className="card-title" style={{ marginBottom: '14px', fontSize: '15px' }}>
            Competitors ({competitors.length})
          </div>

          {competitors.length === 0 && !loading ? (
            <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-dim)', fontSize: '13px' }}>
              No competitors tracked yet. Click "Add Competitor" to start.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {competitors.map((c) => {
                const isSelected = selectedCompetitorId === c.id;
                return (
                  <div
                    key={c.id}
                    onClick={() => setSelectedCompetitorId(c.id)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-md)',
                      background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-card-hover)',
                      border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-main)' }}>{c.name || c.domain}</span>
                      <span className="badge badge-pending" style={{ fontSize: '10.5px' }}>{c.status}</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--accent-cyan)' }}>{c.domain}</div>
                    {c.discovery_reason && (
                      <div style={{ fontSize: '11.5px', color: 'var(--text-dim)', marginTop: '4px' }}>
                        {c.discovery_reason}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Competitor Detail & Pages */}
        <div>
          {selectedCompetitorId ? (
            <>
              <div className="card" style={{ padding: '20px', marginBottom: '20px' }}>
                <div className="card-title" style={{ fontSize: '16px', marginBottom: '12px' }}>
                  Add Competitor Page for Analysis
                </div>
                <form onSubmit={handleAddPage} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>Page URL *</label>
                    <input
                      type="url"
                      className="input"
                      placeholder="https://example.com/blog/article"
                      value={pageUrl}
                      onChange={(e) => setPageUrl(e.target.value)}
                      required
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>Page Title</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="Article Title"
                      value={pageTitle}
                      onChange={(e) => setPageTitle(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div style={{ gridColumn: '1 / -1' }}>
                    <label style={{ fontSize: '12px', color: 'var(--text-dim)', display: 'block', marginBottom: '4px' }}>Content Summary / Target Keyword</label>
                    <input
                      type="text"
                      className="input"
                      placeholder="Summary or key focus areas of this page"
                      value={pageSummary}
                      onChange={(e) => setPageSummary(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end' }}>
                    <button type="submit" className="btn btn-primary btn-sm">
                      <Plus size={14} /> Add Page
                    </button>
                  </div>
                </form>
              </div>

              {/* Analyzed Pages List */}
              <div className="card" style={{ padding: '20px' }}>
                <div className="card-title" style={{ fontSize: '16px', marginBottom: '14px' }}>
                  Analyzed Pages ({pages.length})
                </div>
                {pages.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '30px 0', color: 'var(--text-dim)', fontSize: '13px' }}>
                    No pages added for this competitor yet.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {pages.map((p) => (
                      <div key={p.id} style={{ padding: '12px 14px', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 600, fontSize: '13.5px', color: 'var(--text-main)' }}>
                            {p.title || 'Untitled Page'}
                          </span>
                          <span className="badge badge-approved" style={{ fontSize: '10.5px' }}>{p.page_type}</span>
                        </div>
                        <a
                          href={p.url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontSize: '12px', color: 'var(--accent-cyan)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px' }}
                        >
                          {p.url} <ExternalLink size={12} />
                        </a>
                        {p.content_summary && (
                          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                            {p.content_summary}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '60px 24px', color: 'var(--text-dim)' }}>
              Select a competitor domain on the left to inspect analyzed pages.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
