import React, { useState, useEffect } from 'react';
import { PublishedContent } from '../types';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { Globe, Eye, EyeOff, ExternalLink, ArrowRight } from 'lucide-react';

interface PublishedPageProps {
  onOpenPublicArticle: (slug: string) => void;
}

export const PublishedPage: React.FC<PublishedPageProps> = ({ onOpenPublicArticle }) => {
  const [items, setItems] = useState<PublishedContent[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadPublished = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getPublishedContent();
      setItems(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load published content');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPublished();
  }, []);

  const handleUnpublish = async (id: number, title: string) => {
    if (!window.confirm(`Unpublish "${title}"? The public article URL will no longer be visible to visitors.`)) return;

    try {
      setActionInProgress(id);
      setError(null);
      await api.unpublishContent(id);
      setSuccess(`Article "${title}" unpublished.`);
      loadPublished();
    } catch (err: any) {
      setError(err.message || 'Failed to unpublish');
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <div>
      <div className="card-header" style={{ border: 'none', padding: 0, marginBottom: '24px' }}>
        <div>
          <div className="card-title" style={{ fontSize: '18px' }}>Published Content & Live URLs</div>
          <div className="card-subtitle">Articles published from approved drafts with SEO slugs and public view endpoints</div>
        </div>
      </div>

      {error && <div className="alert-banner alert-error">{error}</div>}
      {success && <div className="alert-banner alert-success">{success}</div>}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Slug & URL</th>
                <th>Publication Date</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && !loading ? (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state">
                      <Globe size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
                      <div className="empty-state-text">No articles published yet. Approve a content draft and click "Publish Article Now".</div>
                    </div>
                  </td>
                </tr>
              ) : (
                items.map((item) => {
                  const isPublished = item.status === 'published';
                  const isWorking = actionInProgress === item.id;

                  return (
                    <tr key={item.id}>
                      <td style={{ color: 'var(--text-dim)', width: '60px' }}>#{item.id}</td>
                      <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                        {item.title}
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12.5px', color: 'var(--accent-cyan)' }}>
                            {item.url}
                          </span>
                        </div>
                      </td>
                      <td style={{ fontSize: '12.5px', color: 'var(--text-dim)' }}>
                        {new Date(item.published_at).toLocaleString()}
                      </td>
                      <td>
                        <StatusBadge status={item.status} />
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                          {isPublished && (
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => onOpenPublicArticle(item.slug)}
                              title="Open public blog view"
                            >
                              <Eye size={13} /> View Article
                            </button>
                          )}

                          {isPublished ? (
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => handleUnpublish(item.id, item.title)}
                              disabled={isWorking}
                              title="Unpublish article"
                            >
                              <EyeOff size={13} /> Unpublish
                            </button>
                          ) : (
                            <span style={{ fontSize: '12px', color: 'var(--text-dim)', fontStyle: 'italic', alignSelf: 'center' }}>
                              Unpublished
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
