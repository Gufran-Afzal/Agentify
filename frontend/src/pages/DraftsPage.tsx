import React, { useState, useEffect } from 'react';
import { ContentDraft, NavView } from '../types';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import {
  FileEdit,
  Save,
  CheckCircle,
  XCircle,
  Globe,
  ArrowRight,
  Eye
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
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

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

  useEffect(() => {
    loadDrafts();
  }, []);

  const selectDraft = (draft: ContentDraft) => {
    setSelectedDraft(draft);
    setTitle(draft.title);
    setIntroduction(draft.introduction);
    setBody(draft.body);
    setConclusion(draft.conclusion);
    setError(null);
    setSuccess(null);
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
        conclusion
      });
      setSelectedDraft(updated);
      setSuccess('Draft updated successfully.');
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
      setSuccess('Draft approved! You can now publish this article.');
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

  const isEditable = selectedDraft?.status === 'draft';
  const isApproved = selectedDraft?.status === 'approved';

  return (
    <div>
      <div className="card-header" style={{ border: 'none', padding: 0, marginBottom: '20px' }}>
        <div>
          <div className="card-title" style={{ fontSize: '18px' }}>Content Drafts & Human Editorial Studio</div>
          <div className="card-subtitle">Review, fine-tune messaging, verify factual consistency, and authorize publishing</div>
        </div>
      </div>

      {error && <div className="alert-banner alert-error">{error}</div>}
      {success && <div className="alert-banner alert-success">{success}</div>}

      {drafts.length === 0 && !loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
          <FileEdit size={40} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
          <div className="card-title" style={{ marginBottom: '6px' }}>No Content Drafts Found</div>
          <div className="card-subtitle">Generate a draft from an approved content brief to begin editing.</div>
          <button className="btn btn-primary" style={{ marginTop: '16px' }} onClick={() => onNavigate('briefs')}>
            View Briefs
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
          {/* Drafts Master List */}
          <div className="card" style={{ padding: '20px' }}>
            <div className="card-title" style={{ fontSize: '15px', marginBottom: '14px' }}>
              Drafts ({drafts.length})
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '700px', overflowY: 'auto' }}>
              {drafts.map((d) => {
                const isSelected = selectedDraft?.id === d.id;
                return (
                  <div
                    key={d.id}
                    onClick={() => selectDraft(d)}
                    style={{
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-md)',
                      background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-card-hover)',
                      border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-subtle)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span style={{ fontSize: '11.5px', color: 'var(--text-dim)' }}>Draft #{d.id}</span>
                      <StatusBadge status={d.status} />
                    </div>
                    <div style={{ fontSize: '13.5px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px', lineHeight: 1.35 }}>
                      {d.title}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--accent-cyan)' }}>
                      Keyword: {d.primary_keyword || 'N/A'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Draft Editor Pane */}
          {selectedDraft ? (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {/* Editor Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '16px', borderBottom: '1px solid var(--border-subtle)' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)' }}>Editorial Studio</h2>
                    <StatusBadge status={selectedDraft.status} />
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '2px' }}>
                    Brief #{selectedDraft.brief_id} • Target Keyword: <strong style={{ color: 'var(--text-main)' }}>{selectedDraft.primary_keyword}</strong>
                  </div>
                </div>

                {/* Workflow State Action Controls */}
                <div style={{ display: 'flex', gap: '8px' }}>
                  {isEditable && (
                    <>
                      <button className="btn btn-secondary btn-sm" onClick={handleSaveChanges} disabled={saving}>
                        <Save size={14} /> Save Changes
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={handleReject} disabled={saving}>
                        <XCircle size={14} /> Reject
                      </button>
                      <button className="btn btn-success btn-sm" onClick={handleApprove} disabled={saving}>
                        <CheckCircle size={14} /> Approve Draft
                      </button>
                    </>
                  )}

                  {isApproved && (
                    <button className="btn btn-primary btn-sm" onClick={handlePublish} disabled={publishing}>
                      <Globe size={14} />
                      {publishing ? 'Publishing...' : 'Publish Article Now'}
                    </button>
                  )}

                  {selectedDraft.status === 'rejected' && (
                    <span style={{ fontSize: '13px', color: 'var(--accent-rose)', alignSelf: 'center', fontStyle: 'italic' }}>
                      Draft Rejected
                    </span>
                  )}
                </div>
              </div>

              {/* Notice if not editable */}
              {!isEditable && (
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', fontSize: '12.5px', color: 'var(--text-dim)' }}>
                  ⓘ This draft is <strong>{selectedDraft.status}</strong>. Content cannot be edited once approved or rejected.
                </div>
              )}

              {/* Title Field */}
              <div className="form-group">
                <label className="form-label">Article Title</label>
                <input
                  className="form-input"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={!isEditable}
                  style={{ fontSize: '16px', fontWeight: 600 }}
                />
              </div>

              {/* Introduction Field */}
              <div className="form-group">
                <label className="form-label">Introduction</label>
                <textarea
                  className="form-textarea"
                  value={introduction}
                  onChange={(e) => setIntroduction(e.target.value)}
                  disabled={!isEditable}
                  rows={3}
                  placeholder="Engaging hook introducing the topic..."
                />
              </div>

              {/* Body Field */}
              <div className="form-group">
                <label className="form-label">Structured Body (Markdown)</label>
                <textarea
                  className="form-textarea"
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  disabled={!isEditable}
                  rows={14}
                  style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '13px', lineHeight: 1.6 }}
                />
              </div>

              {/* Conclusion Field */}
              <div className="form-group">
                <label className="form-label">Conclusion & Key Takeaways</label>
                <textarea
                  className="form-textarea"
                  value={conclusion}
                  onChange={(e) => setConclusion(e.target.value)}
                  disabled={!isEditable}
                  rows={3}
                  placeholder="Summary and product recommendation wrap-up..."
                />
              </div>
            </div>
          ) : (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
              <div className="empty-state">
                <FileEdit size={36} style={{ opacity: 0.4, margin: '0 auto 12px' }} />
                <div className="empty-state-text">Select a draft from the sidebar to open the editor.</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
