import React, { useState, useEffect } from 'react';
import { ContentBrief, NavView } from '../types';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { FileText, Sparkles, Target, Users, ListOrdered, ArrowRight } from 'lucide-react';

interface BriefsPageProps {
  onNavigate: (view: NavView) => void;
}

export const BriefsPage: React.FC<BriefsPageProps> = ({ onNavigate }) => {
  const [briefs, setBriefs] = useState<ContentBrief[]>([]);
  const [loading, setLoading] = useState(false);
  const [generatingId, setGeneratingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadBriefs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getBriefs();
      setBriefs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load briefs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBriefs();
  }, []);

  const handleGenerateDraft = async (briefId: number) => {
    try {
      setGeneratingId(briefId);
      setError(null);
      await api.generateDraft(briefId);
      setSuccess('Content draft generated successfully! Redirecting to Drafts editor...');
      setTimeout(() => onNavigate('drafts'), 900);
    } catch (err: any) {
      setError(err.message || 'Failed to generate draft');
      setGeneratingId(null);
    }
  };

  return (
    <div>
      <div className="card-header" style={{ border: 'none', padding: 0, marginBottom: '24px' }}>
        <div>
          <div className="card-title" style={{ fontSize: '18px' }}>Structured Content Briefs</div>
          <div className="card-subtitle">Comprehensive editorial blueprints detailing search intent, audience, and recommended sections</div>
        </div>
      </div>

      {error && <div className="alert-banner alert-error">{error}</div>}
      {success && <div className="alert-banner alert-success">{success}</div>}

      {briefs.length === 0 && !loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
          <FileText size={40} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
          <div className="card-title" style={{ marginBottom: '6px' }}>No Content Briefs Created Yet</div>
          <div className="card-subtitle">Approve an opportunity to generate a structured content brief.</div>
          <button className="btn btn-primary" style={{ marginTop: '16px' }} onClick={() => onNavigate('opportunities')}>
            View Opportunities
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {briefs.map((b) => {
            const isWorking = generatingId === b.id;
            return (
              <div key={b.id} className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <span style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: 600 }}>Brief #{b.id}</span>
                    <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-main)', marginTop: '4px' }}>
                      {b.title}
                    </h3>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <StatusBadge status={b.status} />
                  </div>
                </div>

                {/* Objective */}
                <p style={{ fontSize: '13.5px', color: 'var(--text-muted)', marginBottom: '20px', lineHeight: 1.6 }}>
                  {b.objective}
                </p>

                {/* Strategy Specs Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px', marginBottom: '20px' }}>
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 16px', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '11.5px', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                      <Target size={13} /> SEARCH INTENT
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-cyan)', textTransform: 'capitalize' }}>
                      {b.search_intent}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 16px', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '11.5px', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                      <Users size={13} /> TARGET AUDIENCE
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
                      {b.target_audience}
                    </div>
                  </div>

                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px 16px', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '11.5px', color: 'var(--text-dim)', marginBottom: '4px' }}>
                      PRIMARY KEYWORD & DEMAND
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>
                      {b.primary_keyword} <span style={{ color: 'var(--accent-cyan)' }}>({b.search_volume.toLocaleString()} /mo)</span>
                    </div>
                  </div>
                </div>

                {/* Recommended Sections */}
                {b.suggested_sections && b.suggested_sections.length > 0 && (
                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: '14px 18px', borderRadius: 'var(--radius-md)', marginBottom: '20px' }}>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                      <ListOrdered size={14} /> RECOMMENDED SECTION OUTLINE
                    </div>
                    <ol style={{ paddingLeft: '20px', fontSize: '13px', color: 'var(--text-muted)' }}>
                      {b.suggested_sections.map((sec, idx) => (
                        <li key={idx} style={{ marginBottom: '4px' }}>{sec}</li>
                      ))}
                    </ol>
                  </div>
                )}

                {/* Action Footer */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
                  {b.status === 'draft' ? (
                    <button
                      className="btn btn-primary"
                      onClick={() => handleGenerateDraft(b.id)}
                      disabled={isWorking}
                    >
                      <Sparkles size={16} />
                      {isWorking ? 'Generating Content Draft...' : 'Generate Draft'}
                    </button>
                  ) : (
                    <button
                      className="btn btn-secondary"
                      onClick={() => onNavigate('drafts')}
                    >
                      <span>Draft Already Generated</span>
                      <ArrowRight size={14} />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
