import React, { useState, useEffect } from 'react';
import { ContentDraft, NavView, QualityAuditResult, ShopifyBlog, PublishToShopifyResult } from '../types';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import {
  FileEdit,
  Save,
  CheckCircle,
  XCircle,
  Globe,
  ShoppingBag,
  Sparkles,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface DraftsPageProps {
  onNavigate: (view: NavView) => void;
}

export const DraftsPage: React.FC<DraftsPageProps> = ({ onNavigate }) => {
  const [drafts, setDrafts] = useState<ContentDraft[]>([]);
  const [selectedDraft, setSelectedDraft] = useState<ContentDraft | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [publishingShopify, setPublishingShopify] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Quality Audit State
  const [audit, setAudit] = useState<QualityAuditResult | null>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [showAuditDetails, setShowAuditDetails] = useState(true);

  // Shopify Publishing State
  const [blogs, setBlogs] = useState<ShopifyBlog[]>([]);
  const [selectedBlogId, setSelectedBlogId] = useState<string>('');
  const [showShopifyModal, setShowShopifyModal] = useState(false);
  const [shopifyResult, setShopifyResult] = useState<PublishToShopifyResult | null>(null);

  // Editor editable fields
  const [title, setTitle] = useState('');
  const [introduction, setIntroduction] = useState('');
  const [body, setBody] = useState('');
  const [conclusion, setConclusion] = useState('');

  const loadDrafts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDrafts();
      setDrafts(data);
      if (data.length > 0 && selectedDraft === null) {
        selectDraft(data[0]);
      } else if (selectedDraft) {
        const fresh = data.find((d) => d.id === selectedDraft.id);
        if (fresh) selectDraft(fresh);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load drafts');
    } finally {
      setLoading(false);
    }
  };

  const loadBlogs = async () => {
    try {
      const b = await api.getStoreBlogs('demo-store');
      setBlogs(b || []);
      if (b && b.length > 0) {
        setSelectedBlogId(b[0].shopify_blog_id);
      }
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadDrafts();
    loadBlogs();
  }, []);

  const loadAudit = async (draftId: number) => {
    setAuditLoading(true);
    try {
      const res = await api.getDraftQualityCheck(draftId);
      setAudit(res);
    } catch {
      setAudit(null);
    } finally {
      setAuditLoading(false);
    }
  };

  const selectDraft = (draft: ContentDraft) => {
    setSelectedDraft(draft);
    setTitle(draft.title);
    setIntroduction(draft.introduction);
    setBody(draft.body);
    setConclusion(draft.conclusion);
    setError(null);
    setSuccess(null);
    setShopifyResult(null);
    loadAudit(draft.id);
  };

  const handleSaveChanges = async () => {
    if (!selectedDraft) return;
    try {
      setSaving(true);
      setError(null);
      const updated = await api.updateDraft(selectedDraft.id, {
        title,
        introduction,
        body,
        conclusion,
      });
      setSelectedDraft(updated);
      setSuccess('Draft updated successfully.');
      loadAudit(updated.id);
      loadDrafts();
    } catch (err: any) {
      setError(err.message || 'Failed to update draft');
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedDraft) return;
    try {
      setSaving(true);
      setError(null);
      await api.approveDraft(selectedDraft.id);
      setSuccess('Draft approved! You can now publish to web or Shopify.');
      await loadDrafts();
    } catch (err: any) {
      setError(err.message || 'Failed to approve draft');
    } finally {
      setSaving(false);
    }
  };

  const handleReject = async () => {
    if (!selectedDraft) return;
    try {
      setSaving(true);
      setError(null);
      await api.rejectDraft(selectedDraft.id);
      setSuccess('Draft rejected.');
      await loadDrafts();
    } catch (err: any) {
      setError(err.message || 'Failed to reject draft');
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = async () => {
    if (!selectedDraft) return;
    try {
      setPublishing(true);
      setError(null);
      const published = await api.publishDraft(selectedDraft.id);
      setSuccess(`Article published successfully at "${published.url}"!`);
      setTimeout(() => onNavigate('published'), 1000);
    } catch (err: any) {
      setError(err.message || 'Publishing failed');
      setPublishing(false);
    }
  };

  const handlePublishToShopify = async () => {
    if (!selectedDraft) return;
    try {
      setPublishingShopify(true);
      setError(null);
      const res = await api.publishDraftToShopify(selectedDraft.id, {
        store_id: 'demo-store',
        blog_id: selectedBlogId || undefined,
      });
      setShopifyResult(res);
      setSuccess(res.message);
      setShowShopifyModal(false);
      loadDrafts();
    } catch (err: any) {
      setError(err.message || 'Failed to publish article to Shopify.');
    } finally {
      setPublishingShopify(false);
    }
  };

  const isEditable = selectedDraft?.status === 'draft';
  const isApproved = selectedDraft?.status === 'approved';

  const getScoreBadgeClass = (score: number) => {
    if (score >= 80) return 'score-badge good';
    if (score >= 65) return 'score-badge ok';
    return 'score-badge poor';
  };

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#fff', letterSpacing: '-0.02em' }}>
          Editorial Studio &amp; Quality Audit
        </h2>
        <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
          Review copy, run automated SEO &amp; brand checks, and publish to Shopify as Draft
        </p>
      </div>

      {error && <div className="alert-banner alert-error">{error}</div>}
      {success && <div className="alert-banner alert-success">{success}</div>}

      {/* Shopify Result Banner */}
      {shopifyResult && (
        <div className="shopify-success-banner" style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <CheckCircle2 size={20} style={{ color: '#34d399', flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 600, color: '#fff', fontSize: '13.5px' }}>{shopifyResult.message}</div>
              <div style={{ fontSize: '12px', color: '#34d399', marginTop: '2px' }}>
                Created as Draft article in Shopify. Review before publishing publicly on your storefront.
              </div>
            </div>
          </div>
          {shopifyResult.admin_url && (
            <a
              href={shopifyResult.admin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-shopify-publish"
              style={{ flexShrink: 0 }}
            >
              <span>Open in Shopify Admin</span>
              <ExternalLink size={13} />
            </a>
          )}
        </div>
      )}

      {drafts.length === 0 && !loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '64px 24px' }}>
          <FileEdit size={40} style={{ margin: '0 auto 12px', opacity: 0.4, color: '#94a3b8', display: 'block' }} />
          <div style={{ fontSize: '17px', fontWeight: 600, color: '#fff', marginBottom: '8px' }}>
            No Content Drafts Found
          </div>
          <div style={{ fontSize: '13.5px', color: '#94a3b8', marginBottom: '16px' }}>
            Generate a draft from an approved content brief to begin editing.
          </div>
          <button className="btn btn-primary" onClick={() => onNavigate('briefs')}>
            View Briefs
          </button>
        </div>
      ) : (
        <div className="drafts-grid">
          {/* Drafts List Sidebar */}
          <div className="card" style={{ padding: '16px' }}>
            <div style={{ fontSize: '13.5px', fontWeight: 600, color: '#e2e8f0', marginBottom: '12px' }}>
              Drafts ({drafts.length})
            </div>
            <div className="draft-sidebar-list">
              {drafts.map((d) => {
                const isSelected = selectedDraft?.id === d.id;
                return (
                  <div
                    key={d.id}
                    onClick={() => selectDraft(d)}
                    className={`draft-list-item${isSelected ? ' selected' : ''}`}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11.5px', fontFamily: 'monospace', color: '#94a3b8' }}>
                        Draft #{d.id}
                      </span>
                      <StatusBadge status={d.status} />
                    </div>
                    <div style={{
                      fontSize: '13.5px', fontWeight: 600, color: '#fff', marginBottom: '4px',
                      display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden'
                    }}>
                      {d.title}
                    </div>
                    <div style={{ fontSize: '12px', color: '#22d3ee', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span>Keyword:</span>
                      <span style={{ fontFamily: 'monospace', color: '#e2e8f0' }}>{d.primary_keyword || 'N/A'}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Draft Editor & Quality Pane */}
          {selectedDraft ? (
            <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Editor Header & Controls */}
              <div style={{
                display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start',
                justifyContent: 'space-between', gap: '16px',
                paddingBottom: '16px', borderBottom: '1px solid rgba(30,41,59,1)'
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <h2 style={{ fontSize: '17px', fontWeight: 700, color: '#fff' }}>{selectedDraft.title}</h2>
                    <StatusBadge status={selectedDraft.status} />
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                    Brief #{selectedDraft.brief_id} • Target Keyword:{' '}
                    <strong style={{ color: '#fff' }}>{selectedDraft.primary_keyword}</strong>
                  </div>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px' }}>
                  {isEditable && (
                    <>
                      <button className="btn btn-secondary btn-sm" onClick={handleSaveChanges} disabled={saving}>
                        <Save size={14} /> Save
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={handleReject} disabled={saving}>
                        <XCircle size={14} /> Reject
                      </button>
                      <button className="btn btn-success btn-sm" onClick={handleApprove} disabled={saving}>
                        <CheckCircle size={14} /> Approve
                      </button>
                    </>
                  )}

                  {isApproved && (
                    <>
                      <button
                        className="btn-shopify-publish"
                        onClick={() => setShowShopifyModal(true)}
                        disabled={publishingShopify}
                      >
                        <ShoppingBag size={14} />
                        <span>Publish to Shopify (Draft)</span>
                      </button>
                      <button className="btn btn-primary btn-sm" onClick={handlePublish} disabled={publishing}>
                        <Globe size={14} />
                        <span>{publishing ? 'Publishing...' : 'Publish Locally'}</span>
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Quality & SEO Audit Scorecard */}
              {audit && (
                <div className="audit-card">
                  <div className="audit-card-header" onClick={() => setShowAuditDetails(!showAuditDetails)}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div className="store-icon-badge indigo">
                        <Sparkles size={16} />
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '13.5px', fontWeight: 600, color: '#fff' }}>Quality &amp; SEO Audit</span>
                          <span className={getScoreBadgeClass(audit.score)}>
                            Score: {audit.score}/100 ({audit.grade})
                          </span>
                        </div>
                        <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                          {audit.word_count} words • Reading Ease: {audit.reading_ease} (Grade {audit.grade_level})
                        </p>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontSize: '12px' }}>
                      <span>{showAuditDetails ? 'Hide details' : 'Show checks'}</span>
                      {showAuditDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>

                  {showAuditDetails && (
                    <div style={{ padding: '0 16px 16px' }}>
                      <div className="audit-checks-grid">
                        {audit.checks.map((c, idx) => (
                          <div key={idx} className={`audit-check-item ${c.passed ? 'passed' : 'failed'}`}>
                            {c.passed ? (
                              <CheckCircle2 size={16} style={{ color: '#34d399', flexShrink: 0, marginTop: '2px' }} />
                            ) : (
                              <AlertTriangle size={16} style={{ color: '#fbbf24', flexShrink: 0, marginTop: '2px' }} />
                            )}
                            <div>
                              <div style={{ fontWeight: 600, color: '#fff', fontSize: '12px' }}>{c.name}</div>
                              <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>{c.message}</div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {audit.matched_products.length > 0 && (
                        <div style={{
                          padding: '10px', background: 'rgba(30,27,75,0.2)',
                          border: '1px solid rgba(99,102,241,0.2)', borderRadius: '8px',
                          fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px'
                        }}>
                          <ShoppingBag size={16} style={{ color: '#818cf8', flexShrink: 0 }} />
                          <span style={{ color: '#cbd5e1' }}>
                            Catalog products detected:{' '}
                            <strong style={{ color: '#fff' }}>{audit.matched_products.join(', ')}</strong>
                          </span>
                        </div>
                      )}

                      {audit.warnings.length > 0 && (
                        <div style={{
                          padding: '10px', background: 'rgba(69,26,3,0.2)',
                          border: '1px solid rgba(245,158,11,0.2)', borderRadius: '8px',
                          fontSize: '12px', marginTop: '8px'
                        }}>
                          <div style={{ fontWeight: 600, color: '#fcd34d', marginBottom: '6px' }}>
                            Actionable Suggestions:
                          </div>
                          <ul style={{ listStyle: 'disc', paddingLeft: '16px', color: '#cbd5e1', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                            {audit.warnings.map((w, i) => (
                              <li key={i} style={{ fontSize: '11px' }}>{w}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Title Field */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label className="shopify-form-label">Article Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={!isEditable}
                  className="shopify-form-input"
                  style={{ fontSize: '15px', fontWeight: 600 }}
                />
              </div>

              {/* Introduction Field */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label className="shopify-form-label">Introduction</label>
                <textarea
                  value={introduction}
                  onChange={(e) => setIntroduction(e.target.value)}
                  disabled={!isEditable}
                  rows={3}
                  className="shopify-form-input"
                  style={{ resize: 'vertical' }}
                  placeholder="Engaging hook introducing the topic..."
                />
              </div>

              {/* Body Field */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label className="shopify-form-label">Structured Body (Markdown)</label>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  disabled={!isEditable}
                  rows={14}
                  className="shopify-form-input font-mono"
                  style={{ lineHeight: '1.65', resize: 'vertical' }}
                />
              </div>

              {/* Conclusion Field */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label className="shopify-form-label">Conclusion &amp; Key Takeaways</label>
                <textarea
                  value={conclusion}
                  onChange={(e) => setConclusion(e.target.value)}
                  disabled={!isEditable}
                  rows={3}
                  className="shopify-form-input"
                  style={{ resize: 'vertical' }}
                  placeholder="Summary and product recommendation wrap-up..."
                />
              </div>
            </div>
          ) : (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
              <div style={{ textAlign: 'center', color: '#94a3b8' }}>
                <FileEdit size={40} style={{ margin: '0 auto 8px', opacity: 0.4, display: 'block' }} />
                <p>Select a draft from the sidebar to open the editor.</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Publish to Shopify Modal */}
      {showShopifyModal && (
        <div className="shopify-modal-overlay">
          <div className="shopify-modal-box" style={{ maxWidth: '420px' }}>
            <div className="shopify-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fff', fontWeight: 600 }}>
                <ShoppingBag size={20} style={{ color: '#34d399' }} />
                <span>Publish to Shopify as Draft</span>
              </div>
              <button
                onClick={() => setShowShopifyModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <div className="shopify-modal-body">
              <p style={{ fontSize: '13.5px', color: '#cbd5e1' }}>
                This will create a new <strong style={{ color: '#fff' }}>Draft Article</strong> on your connected
                Shopify store. You can review and preview it before making it live to shoppers.
              </p>

              <div className="shopify-form-group">
                <label className="shopify-form-label">Target Shopify Blog</label>
                {blogs.length > 0 ? (
                  <select
                    value={selectedBlogId}
                    onChange={(e) => setSelectedBlogId(e.target.value)}
                    className="shopify-form-input"
                  >
                    {blogs.map((b) => (
                      <option key={b.id} value={b.shopify_blog_id}>
                        {b.title} (/blogs/{b.handle})
                      </option>
                    ))}
                  </select>
                ) : (
                  <div style={{
                    fontSize: '12px', color: '#fbbf24', padding: '10px',
                    background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)',
                    borderRadius: '12px'
                  }}>
                    No blogs detected. System will auto-detect your store's primary blog.
                  </div>
                )}
              </div>

              <div className="shopify-modal-footer" style={{ margin: '0 -24px -24px', padding: '12px 24px' }}>
                <button
                  type="button"
                  onClick={() => setShowShopifyModal(false)}
                  className="btn-cancel-ghost"
                >
                  Cancel
                </button>
                <button
                  onClick={handlePublishToShopify}
                  disabled={publishingShopify}
                  className="btn-shopify-connect"
                >
                  {publishingShopify ? 'Publishing...' : 'Create Shopify Draft'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
