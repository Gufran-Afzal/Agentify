import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { StoreStatusResponse, ShopifyBlog } from '../types';
import { StoreConnectModal } from '../components/StoreConnectModal';
import {
  ShoppingBag,
  RefreshCw,
  Plus,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  FileText,
  Package,
  BookOpen,
  ShieldCheck,
} from 'lucide-react';

export const StoreSettingsPage: React.FC = () => {
  const [currentStoreId] = useState('demo-store');
  const [storeStatus, setStoreStatus] = useState<StoreStatusResponse | null>(null);
  const [blogs, setBlogs] = useState<ShopifyBlog[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);

  const loadData = async (storeId: string) => {
    setLoading(true);
    setError(null);
    try {
      const [statusRes, blogsRes] = await Promise.all([
        api.getStoreStatus(storeId).catch(() => null),
        api.getStoreBlogs(storeId).catch(() => []),
      ]);
      if (statusRes) {
        setStoreStatus(statusRes);
      }
      setBlogs(blogsRes || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load store settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(currentStoreId);
  }, [currentStoreId]);

  const handleSync = async () => {
    setSyncing(true);
    setSyncResult(null);
    setError(null);
    try {
      const res = await api.triggerShopifySync(currentStoreId);
      setSyncResult(
        `Synchronized ${res.total_items} items: ${res.products_synced} products, ${res.collections_synced} collections, ${res.articles_synced} articles, and ${res.blogs_synced} blogs.`
      );
      await loadData(currentStoreId);
    } catch (err: any) {
      setError(err.message || 'Failed to complete store sync.');
    } finally {
      setSyncing(false);
    }
  };

  const handleConnectSuccess = (shopName: string) => {
    setSyncResult(`Connected store '${shopName}'! Running initial sync...`);
    loadData(currentStoreId);
  };

  const isConnected = storeStatus?.connection?.status === 'connected';

  return (
    <div>
      {/* Top Banner & Actions */}
      <div className="store-header-banner">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{
              fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
              color: '#34d399', background: 'rgba(16,185,129,0.1)', padding: '2px 10px',
              borderRadius: '9999px', border: '1px solid rgba(16,185,129,0.2)'
            }}>
              Shopify Integration
            </span>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Multi-tenant store operations</span>
          </div>
          <h2 style={{ fontSize: '22px', fontWeight: 700, color: '#fff', letterSpacing: '-0.02em' }}>
            {storeStatus?.store?.name || 'Store Connection'}
          </h2>
          <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
            {storeStatus?.store?.domain
              ? `Connected domain: ${storeStatus.store.domain}`
              : 'Connect your Shopify store to import live catalog products, blogs, and collections.'}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
          <button
            onClick={() => setIsConnectModalOpen(true)}
            className="btn btn-secondary"
            style={{ borderRadius: '12px' }}
          >
            <Plus size={16} style={{ color: '#34d399' }} />
            <span>Connect Store</span>
          </button>
          <button
            onClick={handleSync}
            disabled={syncing || !isConnected}
            className="btn btn-primary"
            style={{ borderRadius: '12px', boxShadow: '0 4px 16px rgba(79,70,229,0.2)' }}
          >
            <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
            <span>{syncing ? 'Syncing Catalog...' : 'Sync Store Data'}</span>
          </button>
        </div>
      </div>

      {/* Alerts */}
      {syncResult && (
        <div className="alert-banner alert-success" style={{ borderRadius: '12px', marginBottom: '20px' }}>
          <CheckCircle2 size={18} style={{ color: '#34d399', flexShrink: 0 }} />
          <div>{syncResult}</div>
        </div>
      )}

      {error && (
        <div className="alert-banner alert-error" style={{ borderRadius: '12px', marginBottom: '20px' }}>
          <AlertCircle size={18} style={{ color: '#fb7185', flexShrink: 0 }} />
          <div>{error}</div>
        </div>
      )}

      {/* KPI Stats Row */}
      <div className="store-kpi-grid">
        <div className="store-kpi-card">
          <div className="store-kpi-label">
            <span>Products Synced</span>
            <Package size={16} style={{ color: '#818cf8' }} />
          </div>
          <div className="store-kpi-value">{loading ? '—' : (storeStatus?.counts?.products ?? 0)}</div>
          <p className="store-kpi-sublabel">Indexed in local research engine</p>
        </div>

        <div className="store-kpi-card">
          <div className="store-kpi-label">
            <span>Collections</span>
            <Layers size={16} style={{ color: '#34d399' }} />
          </div>
          <div className="store-kpi-value">{loading ? '—' : (storeStatus?.counts?.collections ?? 0)}</div>
          <p className="store-kpi-sublabel">Smart &amp; custom collections</p>
        </div>

        <div className="store-kpi-card">
          <div className="store-kpi-label">
            <span>Blog Articles</span>
            <FileText size={16} style={{ color: '#fbbf24' }} />
          </div>
          <div className="store-kpi-value">{loading ? '—' : (storeStatus?.counts?.existing_articles ?? 0)}</div>
          <p className="store-kpi-sublabel">Checked to prevent duplicate topics</p>
        </div>

        <div className="store-kpi-card">
          <div className="store-kpi-label">
            <span>Shopify Blogs</span>
            <BookOpen size={16} style={{ color: '#22d3ee' }} />
          </div>
          <div className="store-kpi-value">{loading ? '—' : (storeStatus?.counts?.blogs ?? 0)}</div>
          <p className="store-kpi-sublabel">Available publishing channels</p>
        </div>
      </div>

      {/* Connection & Security + Blogs */}
      <div className="store-main-grid">
        {/* Connection Status Card */}
        <div className="store-status-card">
          <div className="store-status-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div className="store-icon-badge indigo">
                <ShoppingBag size={18} />
              </div>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>Shopify Connection Status</h3>
                <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>Authenticated with Admin API</p>
              </div>
            </div>

            <span className={isConnected ? 'status-pill-connected' : 'status-pill-disconnected'}>
              {isConnected ? '● Connected' : '○ Not Connected'}
            </span>
          </div>

          <div className="store-info-grid">
            <div className="store-info-item">
              <div className="store-info-label">Store Domain</div>
              <div className="store-info-value" style={{ fontFamily: 'monospace' }}>
                {storeStatus?.store?.domain || 'Not configured'}
              </div>
            </div>

            <div className="store-info-item">
              <div className="store-info-label">Last Synced</div>
              <div className="store-info-value" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Clock size={13} style={{ color: '#94a3b8' }} />
                <span>
                  {storeStatus?.connection?.last_synced_at
                    ? new Date(storeStatus.connection.last_synced_at).toLocaleString()
                    : 'Never'}
                </span>
              </div>
            </div>

            <div className="store-info-item">
              <div className="store-info-label">Sync Engine Status</div>
              <div className="store-info-value" style={{ textTransform: 'capitalize' }}>
                {storeStatus?.connection?.sync_status || 'idle'}
              </div>
            </div>

            <div className="store-info-item">
              <div className="store-info-label">Platform</div>
              <div className="store-info-value" style={{ textTransform: 'capitalize' }}>
                {storeStatus?.store?.platform || 'demo'}
              </div>
            </div>
          </div>

          <div className="store-security-bar">
            <ShieldCheck size={16} style={{ color: '#818cf8', flexShrink: 0 }} />
            <span>
              Credentials are encrypted using AES-128 Fernet cryptography. Raw API access tokens are never transmitted to the browser.
            </span>
          </div>
        </div>

        {/* Available Blogs Card */}
        <div className="store-blogs-card">
          <div style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            paddingBottom: '12px', borderBottom: '1px solid rgba(30,41,59,0.8)',
            marginBottom: '16px'
          }}>
            <BookOpen size={16} style={{ color: '#22d3ee' }} />
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>Target Blogs</h3>
          </div>

          {blogs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: '#64748b', fontSize: '12px' }}>
              <p>No Shopify blogs synced yet.</p>
              <p style={{ marginTop: '4px' }}>Connect your store or click "Sync Store Data" to load blogs.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {blogs.map((b) => (
                <div key={b.id} className="store-blog-item">
                  <div>
                    <div style={{ fontWeight: 600, color: '#fff', fontSize: '13px' }}>{b.title}</div>
                    <div style={{ color: '#64748b', fontFamily: 'monospace', fontSize: '11px', marginTop: '2px' }}>
                      /blogs/{b.handle}
                    </div>
                  </div>
                  <span className="tag-pill">ID #{b.shopify_blog_id}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Connect Modal */}
      <StoreConnectModal
        isOpen={isConnectModalOpen}
        onClose={() => setIsConnectModalOpen(false)}
        onSuccess={handleConnectSuccess}
      />
    </div>
  );
};
