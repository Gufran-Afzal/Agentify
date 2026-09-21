import React, { useState, useEffect } from 'react';
import { ResearchRun, Opportunity } from '../types';
import { api } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { FlaskConical, Play, CheckCircle2, XCircle, ChevronRight, Layers } from 'lucide-react';

export const ResearchPage: React.FC = () => {
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [loadingOpps, setLoadingOpps] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadRuns = async () => {
    try {
      setLoadingRuns(true);
      setError(null);
      const data = await api.getResearchRuns();
      setRuns(data);
      if (data.length > 0 && selectedRunId === null) {
        setSelectedRunId(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load research runs');
    } finally {
      setLoadingRuns(false);
    }
  };

  const loadOpportunities = async (runId: number) => {
    try {
      setLoadingOpps(true);
      const opps = await api.getRunOpportunities(runId);
      setOpportunities(opps);
    } catch (err: any) {
      setError(err.message || 'Failed to load opportunities for run');
    } finally {
      setLoadingOpps(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  useEffect(() => {
    if (selectedRunId !== null) {
      loadOpportunities(selectedRunId);
    }
  }, [selectedRunId]);

  const handleRunResearch = async () => {
    try {
      setExecuting(true);
      setError(null);
      setSuccess(null);

      // 1. Create run
      const createdRun = await api.createResearchRun();

      // 2. Execute run
      const execResult = await api.executeResearchRun(createdRun.id);

      setSuccess(`Research Run #${createdRun.id} executed successfully! Found ${execResult.opportunities_count} content opportunities.`);
      await loadRuns();
      setSelectedRunId(createdRun.id);
      setOpportunities(execResult.opportunities);
    } catch (err: any) {
      setError(err.message || 'Research run execution failed');
    } finally {
      setExecuting(false);
    }
  };

  const handleApproveOpp = async (oppId: number) => {
    try {
      await api.approveOpportunity(oppId);
      setSuccess('Opportunity approved!');
      if (selectedRunId) loadOpportunities(selectedRunId);
    } catch (err: any) {
      setError(err.message || 'Failed to approve opportunity');
    }
  };

  const handleRejectOpp = async (oppId: number) => {
    try {
      await api.rejectOpportunity(oppId);
      setSuccess('Opportunity rejected.');
      if (selectedRunId) loadOpportunities(selectedRunId);
    } catch (err: any) {
      setError(err.message || 'Failed to reject opportunity');
    }
  };

  return (
    <div>
      {/* Action Header */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '20px 24px', marginBottom: '24px' }}>
        <div>
          <div className="card-title" style={{ fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FlaskConical size={20} color="var(--primary)" />
            <span>Autonomous Content Opportunity Discovery</span>
          </div>
          <div className="card-subtitle">
            Inspects product catalog against search demand signals and audits existing content for duplicate suppression.
          </div>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleRunResearch}
          disabled={executing}
          style={{ padding: '11px 22px', fontSize: '14px' }}
        >
          <Play size={16} />
          {executing ? 'Executing Research Run...' : 'Run Research'}
        </button>
      </div>

      {error && <div className="alert-banner alert-error">{error}</div>}
      {success && <div className="alert-banner alert-success">{success}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '24px' }}>
        {/* Runs History List */}
        <div className="card" style={{ padding: '20px' }}>
          <div className="card-title" style={{ marginBottom: '14px', fontSize: '15px' }}>
            Research History ({runs.length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '550px', overflowY: 'auto' }}>
            {runs.length === 0 && !loadingRuns && (
              <div className="empty-state" style={{ padding: '20px 0' }}>
                <div style={{ fontSize: '13px', color: 'var(--text-dim)' }}>No runs yet. Click "Run Research" to start.</div>
              </div>
            )}

            {runs.map((r) => {
              const isSelected = selectedRunId === r.id;
              return (
                <div
                  key={r.id}
                  onClick={() => setSelectedRunId(r.id)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: 'var(--radius-md)',
                    background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-card-hover)',
                    border: isSelected ? '1px solid var(--primary)' : '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-main)' }}>Run #{r.id}</span>
                    <StatusBadge status={r.status} />
                  </div>
                  <div style={{ fontSize: '11.5px', color: 'var(--text-dim)' }}>
                    Started: {new Date(r.created_at).toLocaleTimeString()}
                  </div>
                  {r.completed_at && (
                    <div style={{ fontSize: '11.5px', color: 'var(--text-dim)' }}>
                      Completed: {new Date(r.completed_at).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Opportunities Generated for Selected Run */}
        <div>
          <div className="card-header" style={{ border: 'none', padding: 0, marginBottom: '16px' }}>
            <div>
              <div className="card-title" style={{ fontSize: '17px' }}>
                {selectedRunId ? `Opportunities in Run #${selectedRunId}` : 'Select a Research Run'}
              </div>
              <div className="card-subtitle">
                {opportunities.length} candidate topic(s) discovered with transparent scoring & evidence
              </div>
            </div>
          </div>

          {loadingOpps ? (
            <div className="card" style={{ textAlign: 'center', padding: '40px' }}>Loading opportunities...</div>
          ) : opportunities.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '48px' }}>
              <Layers size={36} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
              <div className="empty-state-text">No opportunities found for this run or all catalog topics are already satisfied.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {opportunities.map((opp) => (
                <div key={opp.id} className="card" style={{ margin: 0, padding: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px' }}>
                    <div>
                      <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
                        {opp.title}
                      </div>
                      <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                        {opp.reason}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span className={`badge badge-${opp.confidence === 'high' ? 'approved' : opp.confidence === 'medium' ? 'pending' : 'draft'}`}>
                        {opp.confidence} confidence
                      </span>
                      <StatusBadge status={opp.status} />
                    </div>
                  </div>

                  {/* Metadata Chips */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginBottom: '14px', fontSize: '12.5px' }}>
                    <div style={{ background: 'rgba(255,255,255,0.04)', padding: '4px 10px', borderRadius: '6px' }}>
                      Primary Keyword: <strong style={{ color: 'var(--text-main)' }}>{opp.primary_keyword || 'N/A'}</strong>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.04)', padding: '4px 10px', borderRadius: '6px' }}>
                      Search Demand: <strong style={{ color: 'var(--accent-cyan)' }}>{opp.search_volume.toLocaleString()} /mo</strong>
                    </div>
                  </div>

                  {/* Evidence Items */}
                  {opp.evidence && opp.evidence.length > 0 && (
                    <div style={{ background: 'rgba(0,0,0,0.25)', padding: '12px 16px', borderRadius: 'var(--radius-md)', marginBottom: '16px' }}>
                      <div style={{ fontSize: '11.5px', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '6px' }}>
                        Scoring Evidence & Signals:
                      </div>
                      <ul style={{ paddingLeft: '18px', fontSize: '12.5px', color: 'var(--text-muted)' }}>
                        {opp.evidence.map((ev, idx) => (
                          <li key={idx} style={{ marginBottom: '2px' }}>{ev}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Action Buttons */}
                  {opp.status === 'pending' && (
                    <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleRejectOpp(opp.id)}
                      >
                        <XCircle size={14} /> Reject
                      </button>
                      <button
                        className="btn btn-success btn-sm"
                        onClick={() => handleApproveOpp(opp.id)}
                      >
                        <CheckCircle2 size={14} /> Approve Opportunity
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
