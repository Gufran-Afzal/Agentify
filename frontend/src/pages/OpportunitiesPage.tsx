import React, { useState, useEffect } from 'react';
import { Opportunity, NavView } from '../types';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { Lightbulb, CheckCircle2, XCircle, FilePlus, Filter } from 'lucide-react';

interface OpportunitiesPageProps {
  onNavigate: (view: NavView) => void;
}

export const OpportunitiesPage: React.FC<OpportunitiesPageProps> = ({ onNavigate }) => {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');
  const [loading, setLoading] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadOpportunities = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getOpportunities(filter === 'all' ? undefined : filter);
      setOpportunities(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load opportunities');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOpportunities();
  }, [filter]);

  const handleApprove = async (id: number) => {
    try {
      setActionInProgress(id);
      setError(null);
      await api.approveOpportunity(id);
      setSuccess('Opportunity approved! You can now create a Content Brief.');
      loadOpportunities();
    } catch (err: any) {
      setError(err.message || 'Failed to approve');
    } finally {
      setActionInProgress(null);
    }
  };

  const handleReject = async (id: number) => {
    try {
      setActionInProgress(id);
      setError(null);
      await api.rejectOpportunity(id);
      setSuccess('Opportunity rejected.');
      loadOpportunities();
    } catch (err: any) {
      setError(err.message || 'Failed to reject');
    } finally {
      setActionInProgress(null);
    }
  };

  const handleCreateBrief = async (id: number) => {
    try {
      setActionInProgress(id);
      setError(null);
      await api.createBrief(id);
      setSuccess('Content brief generated successfully! Redirecting to Briefs...');
      setTimeout(() => onNavigate('briefs'), 800);
    } catch (err: any) {
      setError(err.message || 'Failed to create brief');
      setActionInProgress(null);
    }
  };

  return (
    <div>
      {/* Header & Filter Controls */}
      <div className="card-header" style={{ border: 'none', padding: 0, marginBottom: '24px' }}>
        <div>
          <div className="card-title" style={{ fontSize: '18px' }}>Content Opportunities</div>
          <div className="card-subtitle">Scored opportunities discovered from catalog gaps and search trends</div>
        </div>

        {/* Status Filter Tabs */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(255,255,255,0.04)', padding: '4px', borderRadius: 'var(--radius-md)' }}>
          {(['all', 'pending', 'approved', 'rejected'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className="btn btn-sm"
              style={{
                background: filter === tab ? 'var(--primary)' : 'transparent',
                color: filter === tab ? '#fff' : 'var(--text-muted)',
                textTransform: 'capitalize'
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="alert-banner alert-error">{error}</div>}
      {success && <div className="alert-banner alert-success">{success}</div>}

      {/* Opportunities List */}
      {opportunities.length === 0 && !loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
          <Lightbulb size={40} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
          <div className="card-title" style={{ marginBottom: '6px' }}>No {filter !== 'all' ? filter : ''} opportunities found</div>
          <div className="card-subtitle">Run a new research scan to discover content gaps.</div>
          <button className="btn btn-primary" style={{ marginTop: '16px' }} onClick={() => onNavigate('research')}>
            Go to Research
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '20px' }}>
          {opportunities.map((opp) => {
            const isPending = opp.status === 'pending';
            const isApproved = opp.status === 'approved';
            const isWorking = actionInProgress === opp.id;

            return (
              <div key={opp.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: 600 }}>Run #{opp.research_run_id}</span>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <span className={`badge badge-${opp.confidence === 'high' ? 'approved' : opp.confidence === 'medium' ? 'pending' : 'draft'}`}>
                        {opp.confidence}
                      </span>
                      <StatusBadge status={opp.status} />
                    </div>
                  </div>

                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
                    {opp.title}
                  </div>

                  <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '14px' }}>
                    {opp.reason}
                  </p>

                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '16px', fontSize: '12px' }}>
                    <span style={{ background: 'rgba(255,255,255,0.05)', padding: '3px 8px', borderRadius: '4px' }}>
                      Keyword: <strong style={{ color: 'var(--text-main)' }}>{opp.primary_keyword || 'N/A'}</strong>
                    </span>
                    <span style={{ background: 'rgba(255,255,255,0.05)', padding: '3px 8px', borderRadius: '4px' }}>
                      Demand: <strong style={{ color: 'var(--accent-cyan)' }}>{opp.search_volume.toLocaleString()} searches/mo</strong>
                    </span>
                  </div>

                  {opp.evidence && opp.evidence.length > 0 && (
                    <div style={{ background: 'rgba(0,0,0,0.25)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', marginBottom: '16px' }}>
                      <div style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '4px' }}>
                        Evidence & Audit Signals:
                      </div>
                      <ul style={{ paddingLeft: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {opp.evidence.map((ev, i) => (
                          <li key={i}>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Valid Actions based strictly on state machine */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '14px', borderTop: '1px solid var(--border-subtle)' }}>
                  {isPending && (
                    <>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleReject(opp.id)}
                        disabled={isWorking}
                      >
                        <XCircle size={14} /> Reject
                      </button>
                      <button
                        className="btn btn-success btn-sm"
                        onClick={() => handleApprove(opp.id)}
                        disabled={isWorking}
                      >
                        <CheckCircle2 size={14} /> Approve
                      </button>
                    </>
                  )}

                  {isApproved && (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleCreateBrief(opp.id)}
                      disabled={isWorking}
                    >
                      <FilePlus size={14} />
                      {isWorking ? 'Generating Brief...' : 'Create Content Brief'}
                    </button>
                  )}

                  {opp.status === 'rejected' && (
                    <span style={{ fontSize: '12px', color: 'var(--accent-rose)', fontStyle: 'italic' }}>
                      Rejected — no further action
                    </span>
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
