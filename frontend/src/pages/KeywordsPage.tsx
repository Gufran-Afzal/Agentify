import React, { useState, useEffect } from 'react';
import { Keyword } from '../types';
import { api } from '../api/client';
import { Modal } from '../components/Modal';
import { Plus, Trash2, Search, Info } from 'lucide-react';

export const KeywordsPage: React.FC = () => {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modal form state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [keywordText, setKeywordText] = useState('');
  const [searchVolume, setSearchVolume] = useState<number | ''>(5000);
  const [submitting, setSubmitting] = useState(false);

  const loadKeywords = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getKeywords();
      setKeywords(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load keywords');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKeywords();
  }, []);

  const handleAddKeyword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keywordText.trim() || searchVolume === '') return;

    try {
      setSubmitting(true);
      setError(null);
      await api.createKeyword({
        keyword: keywordText.trim(),
        search_volume: Number(searchVolume)
      });
      setSuccess(`Keyword "${keywordText}" added.`);
      setIsModalOpen(false);
      setKeywordText('');
      setSearchVolume(5000);
      loadKeywords();
    } catch (err: any) {
      setError(err.message || 'Failed to create keyword');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number, kwName: string) => {
    if (!window.confirm(`Are you sure you want to remove "${kwName}"?`)) return;

    try {
      await api.deleteKeyword(id);
      setSuccess(`Keyword "${kwName}" removed.`);
      loadKeywords();
    } catch (err: any) {
      setError(err.message || 'Failed to delete keyword');
    }
  };

  return (
    <div>
      <div className="card-header" style={{ border: 'none', padding: 0, marginBottom: '20px' }}>
        <div>
          <div className="card-title" style={{ fontSize: '18px' }}>Search Demand & Keywords</div>
          <div className="card-subtitle">Estimated monthly search volume used by the opportunity scoring engine</div>
        </div>
        <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
          <Plus size={16} /> Add Keyword
        </button>
      </div>

      <div className="alert-banner" style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.25)', color: '#67e8f9' }}>
        <Info size={16} />
        <span>
          <strong>Mock / Demo Data:</strong> Keyword search volumes shown below represent calibrated seed data for the MVP. The system architecture is built to seamlessly swap in live Search Console or third-party keyword APIs without database changes.
        </span>
      </div>

      {error && <div className="alert-banner alert-error">{error}</div>}
      {success && <div className="alert-banner alert-success">{success}</div>}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Keyword Target</th>
                <th>Monthly Search Volume</th>
                <th>Source</th>
                <th>Created</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {keywords.length === 0 && !loading ? (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state">
                      <Search size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
                      <div className="empty-state-text">No keywords found.</div>
                    </div>
                  </td>
                </tr>
              ) : (
                keywords.map((k) => (
                  <tr key={k.id}>
                    <td style={{ color: 'var(--text-dim)', width: '60px' }}>#{k.id}</td>
                    <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>{k.keyword}</td>
                    <td style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>
                      {k.search_volume.toLocaleString()} searches/mo
                    </td>
                    <td>
                      <span className="badge badge-draft">Demo / Seed</span>
                    </td>
                    <td style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                      {new Date(k.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDelete(k.id, k.keyword)}
                        title="Delete keyword"
                      >
                        <Trash2 size={13} /> Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Keyword Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add Target Keyword"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button
              className="btn btn-primary"
              onClick={handleAddKeyword}
              disabled={submitting || !keywordText.trim() || searchVolume === ''}
            >
              {submitting ? 'Saving...' : 'Save Keyword'}
            </button>
          </>
        }
      >
        <form onSubmit={handleAddKeyword}>
          <div className="form-group">
            <label className="form-label">Keyword Query *</label>
            <input
              className="form-input"
              value={keywordText}
              onChange={(e) => setKeywordText(e.target.value)}
              placeholder="e.g. retinol vs bakuchiol for sensitive skin"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Estimated Monthly Search Volume *</label>
            <input
              type="number"
              className="form-input"
              value={searchVolume}
              onChange={(e) => setSearchVolume(e.target.value === '' ? '' : Number(e.target.value))}
              placeholder="e.g. 8500"
              min="0"
              required
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};
