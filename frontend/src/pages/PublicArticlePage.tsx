import React, { useState, useEffect } from 'react';
import { PublicArticle, NavView } from '../types';
import { api } from '../api/client';
import { ArrowLeft, Calendar, Tag, AlertTriangle } from 'lucide-react';

interface PublicArticlePageProps {
  slug: string;
  onBack: () => void;
}

export const PublicArticlePage: React.FC<PublicArticlePageProps> = ({ slug, onBack }) => {
  const [article, setArticle] = useState<PublicArticle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getPublicArticle(slug);
        setArticle(data);
      } catch (err: any) {
        setError(err.message || 'Article not found or not publicly published.');
      } finally {
        setLoading(false);
      }
    };

    if (slug) {
      fetchArticle();
    }
  }, [slug]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 20px' }}>
        <div style={{ fontSize: '16px', color: 'var(--text-muted)' }}>Loading article...</div>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="public-article-container" style={{ textAlign: 'center', padding: '60px 40px' }}>
        <AlertTriangle size={48} color="var(--accent-rose)" style={{ margin: '0 auto 16px' }} />
        <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#fff', marginBottom: '10px' }}>
          404 — Content Not Available
        </h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '24px' }}>
          {error || 'The requested article does not exist or has been unpublished by store editors.'}
        </p>
        <button className="btn btn-secondary" onClick={onBack}>
          <ArrowLeft size={16} /> Return to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <button className="btn btn-secondary btn-sm" onClick={onBack}>
          <ArrowLeft size={14} /> Back to Dashboard
        </button>
      </div>

      <article className="public-article-container">
        <header className="article-header">
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '14px' }}>
            <span style={{ fontSize: '12px', background: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc', padding: '3px 10px', borderRadius: '999px', fontWeight: 600 }}>
              Live Store Article
            </span>
            {article.primary_keyword && (
              <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12.5px', color: 'var(--accent-cyan)' }}>
                <Tag size={13} /> {article.primary_keyword}
              </span>
            )}
          </div>

          <h1 className="article-title">{article.title}</h1>

          <div className="article-meta">
            <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Calendar size={13} /> Published on {new Date(article.published_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
            </span>
            <span>•</span>
            <span>SEO Slug: <code>/blog/{article.slug}</code></span>
          </div>
        </header>

        {/* Introduction */}
        {article.introduction && (
          <div className="article-intro">
            {article.introduction}
          </div>
        )}

        {/* Structured Markdown Body */}
        <div className="article-body">
          {article.body}
        </div>

        {/* Conclusion */}
        {article.conclusion && (
          <div className="article-conclusion">
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px', color: '#fff' }}>
              Takeaway & Editorial Note
            </h3>
            {article.conclusion}
          </div>
        )}
      </article>
    </div>
  );
};
