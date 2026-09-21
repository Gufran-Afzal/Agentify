import React, { useState, useEffect } from 'react';
import { Product } from '../types';
import { api } from '../api/client';
import { Modal } from '../components/Modal';
import { Plus, Trash2, Package } from 'lucide-react';

export const ProductsPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modal form state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getProducts();
      setProducts(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleAddProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !category.trim() || !description.trim()) return;

    try {
      setSubmitting(true);
      setError(null);
      await api.createProduct({
        name: name.trim(),
        category: category.trim(),
        description: description.trim()
      });
      setSuccess(`Product "${name}" added to catalog.`);
      setIsModalOpen(false);
      setName('');
      setCategory('');
      setDescription('');
      loadProducts();
    } catch (err: any) {
      setError(err.message || 'Failed to create product');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number, prodName: string) => {
    if (!window.confirm(`Are you sure you want to remove "${prodName}" from the catalog?`)) return;

    try {
      await api.deleteProduct(id);
      setSuccess(`Product "${prodName}" deleted.`);
      loadProducts();
    } catch (err: any) {
      setError(err.message || 'Failed to delete product');
    }
  };

  return (
    <div>
      <div className="card-header" style={{ border: 'none', padding: 0, marginBottom: '24px' }}>
        <div>
          <div className="card-title" style={{ fontSize: '18px' }}>Store Product Catalog</div>
          <div className="card-subtitle">Products analyzed for organic search demand and topic relevance</div>
        </div>
        <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
          <Plus size={16} /> Add Product
        </button>
      </div>

      {error && <div className="alert-banner alert-error">{error}</div>}
      {success && <div className="alert-banner alert-success">{success}</div>}

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Product Name</th>
                <th>Category</th>
                <th>Description</th>
                <th>Created</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 && !loading ? (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state">
                      <Package size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
                      <div className="empty-state-text">No products found in catalog.</div>
                    </div>
                  </td>
                </tr>
              ) : (
                products.map((p) => (
                  <tr key={p.id}>
                    <td style={{ color: 'var(--text-dim)', width: '60px' }}>#{p.id}</td>
                    <td style={{ fontWeight: 600, color: 'var(--text-main)' }}>{p.name}</td>
                    <td>
                      <span className="badge badge-draft">{p.category}</span>
                    </td>
                    <td style={{ maxWidth: '400px', fontSize: '13px' }}>{p.description}</td>
                    <td style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                      {new Date(p.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDelete(p.id, p.name)}
                        title="Delete product"
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

      {/* Add Product Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Add New Store Product"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button
              className="btn btn-primary"
              onClick={handleAddProduct}
              disabled={submitting || !name.trim() || !category.trim() || !description.trim()}
            >
              {submitting ? 'Saving...' : 'Save Product'}
            </button>
          </>
        }
      >
        <form onSubmit={handleAddProduct}>
          <div className="form-group">
            <label className="form-label">Product Name *</label>
            <input
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Squalane Cleanser"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Category *</label>
            <input
              className="form-input"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g. Cleansers, Serums, Moisturizers"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Description *</label>
            <textarea
              className="form-textarea"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe primary ingredients, target skin concerns, and benefits..."
              required
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};
