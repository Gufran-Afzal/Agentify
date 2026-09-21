import React, { useState } from 'react';
import { api } from '../api/client';
import { ShoppingBag, Key, Globe, CheckCircle2, AlertCircle, Loader2, X } from 'lucide-react';

interface StoreConnectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (shopName: string) => void;
}

export const StoreConnectModal: React.FC<StoreConnectModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [storeId, setStoreId] = useState('shopify-store');
  const [shopDomain, setShopDomain] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [apiVersion, setApiVersion] = useState('2024-04');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shopDomain.trim() || !accessToken.trim()) {
      setError('Please provide both your Shopify store domain and Admin API access token.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.connectShopifyToken({
        store_id: storeId.trim() || 'shopify-store',
        shop_domain: shopDomain.trim(),
        access_token: accessToken.trim(),
        api_version: apiVersion,
      });

      onSuccess(res.shop_name);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Shopify store.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="shopify-modal-overlay">
      <div className="shopify-modal-box">
        {/* Header */}
        <div className="shopify-modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div className="store-icon-badge emerald" style={{ width: '40px', height: '40px', borderRadius: '10px' }}>
              <ShoppingBag size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '17px', fontWeight: 600, color: '#fff' }}>Connect Shopify Store</h3>
              <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                Sync products, collections, and publish draft articles
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: '6px', color: '#94a3b8', background: 'transparent',
              border: 'none', borderRadius: '8px', cursor: 'pointer', transition: 'color 0.2s'
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#fff')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#94a3b8')}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="shopify-modal-body">
          {error && (
            <div className="alert-banner alert-error" style={{ borderRadius: '12px' }}>
              <AlertCircle size={18} style={{ color: '#fb7185', flexShrink: 0 }} />
              <div>{error}</div>
            </div>
          )}

          <div className="shopify-form-group">
            <label className="shopify-form-label">Store Identifier</label>
            <input
              type="text"
              value={storeId}
              onChange={(e) => setStoreId(e.target.value)}
              placeholder="e.g. main-store"
              className="shopify-form-input"
              required
            />
          </div>

          <div className="shopify-form-group">
            <label className="shopify-form-label">Shop Domain (myshopify.com)</label>
            <div className="shopify-form-input-icon">
              <Globe size={16} className="icon" />
              <input
                type="text"
                value={shopDomain}
                onChange={(e) => setShopDomain(e.target.value)}
                placeholder="brand-name.myshopify.com"
                className="shopify-form-input"
                required
              />
            </div>
          </div>

          <div className="shopify-form-group">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <label className="shopify-form-label">Admin API Access Token</label>
              <button
                type="button"
                onClick={() => setShowHelp(!showHelp)}
                style={{
                  fontSize: '12px', color: '#818cf8', background: 'transparent',
                  border: 'none', cursor: 'pointer', transition: 'color 0.2s'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#a5b4fc')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#818cf8')}
              >
                How to get token?
              </button>
            </div>
            <div className="shopify-form-input-icon">
              <Key size={16} className="icon" />
              <input
                type="password"
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                placeholder="shpat_xxxxxxxxxxxxxxxxxxxxxxxx"
                className="shopify-form-input font-mono"
                required
              />
            </div>
          </div>

          {showHelp && (
            <div className="help-box">
              <p style={{ fontWeight: 600, color: '#a5b4fc', marginBottom: '8px' }}>
                How to create a Custom App Token:
              </p>
              <ol>
                <li>In your Shopify Admin, click <strong style={{ color: '#fff' }}>Settings</strong> &gt; <strong style={{ color: '#fff' }}>Apps and sales channels</strong>.</li>
                <li>Click <strong style={{ color: '#fff' }}>Develop apps</strong> and then <strong style={{ color: '#fff' }}>Create an app</strong>.</li>
                <li>Under <strong style={{ color: '#fff' }}>Configuration</strong>, select <strong style={{ color: '#fff' }}>Admin API integration</strong>.</li>
                <li>
                  Grant scopes:{' '}
                  <code style={{ background: 'rgba(0,0,0,0.4)', padding: '1px 4px', borderRadius: '3px', color: '#a5b4fc' }}>read_products</code>,{' '}
                  <code style={{ background: 'rgba(0,0,0,0.4)', padding: '1px 4px', borderRadius: '3px', color: '#a5b4fc' }}>write_products</code>,{' '}
                  <code style={{ background: 'rgba(0,0,0,0.4)', padding: '1px 4px', borderRadius: '3px', color: '#a5b4fc' }}>read_content</code>,{' '}
                  <code style={{ background: 'rgba(0,0,0,0.4)', padding: '1px 4px', borderRadius: '3px', color: '#a5b4fc' }}>write_content</code>.
                </li>
                <li>
                  Click <strong style={{ color: '#fff' }}>Install app</strong> and copy the token (
                  <code style={{ color: '#fcd34d' }}>shpat_...</code>).
                </li>
              </ol>
            </div>
          )}

          <div className="shopify-modal-footer" style={{ margin: '0 -24px -24px', padding: '12px 24px' }}>
            <button type="button" onClick={onClose} className="btn-cancel-ghost">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-shopify-connect">
              {loading ? (
                <>
                  <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                  <span>Verifying with Shopify...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 size={16} />
                  <span>Connect &amp; Verify</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
