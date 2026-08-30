'use client';
import { useEffect, useState } from 'react';
import { listWebhookEndpoints, createWebhookEndpoint, deleteWebhookEndpoint } from '@/lib/api';

export default function IntegrationsView() {
  const [endpoints, setEndpoints] = useState<any[]>([]);
  const [newUrl, setNewUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);

  useEffect(() => {
    fetchEndpoints();
  }, []);

  const fetchEndpoints = async () => {
    try {
      const data = await listWebhookEndpoints();
      setEndpoints(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!newUrl) return;
    try {
      const data = await createWebhookEndpoint(newUrl);
      setEndpoints([...endpoints, data]);
      setNewUrl('');
      setCreatedSecret(data.secret);
    } catch (e) {
      alert("Failed to create webhook endpoint.");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteWebhookEndpoint(id);
      setEndpoints(endpoints.filter(e => e.id !== id));
    } catch (e) {
      alert("Failed to delete webhook endpoint.");
    }
  };

  if (loading) return <div className="container"><p>Loading integrations...</p></div>;

  return (
    <div className="container">
      <div className="header">
        <h1 className="title">Customer Integrations</h1>
        <p className="text-secondary">Manage your external connections and webhooks.</p>
      </div>

      {createdSecret && (
        <div style={{ padding: '1rem', background: 'var(--status-high)', color: '#000', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontWeight: 600 }}>
          Webhook Created! Your HMAC Signing Secret is: <br/><br/>
          <code style={{ background: 'rgba(0,0,0,0.1)', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>{createdSecret}</code><br/><br/>
          Please copy this now. It will not be shown again.
          <button className="button" style={{ marginLeft: '1rem', borderColor: '#000', color: '#000' }} onClick={() => setCreatedSecret(null)}>Dismiss</button>
        </div>
      )}

      <div className="case-grid">
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3>Payment Gateway (Simulator)</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'var(--status-low)' }}></div>
            <strong>Connected</strong>
          </div>
          
          <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span className="text-secondary">Traffic Simulator</span>
              <strong>Active</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span className="text-secondary">Expected Schema</span>
              <strong>RiskPilot Core v1</strong>
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3>Outbound Webhooks</h3>
          <p className="text-secondary">Receive real-time risk assessments directly to your systems.</p>
          
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <input 
              type="text" 
              placeholder="https://your-system.com/webhook" 
              value={newUrl}
              onChange={e => setNewUrl(e.target.value)}
              style={{ flex: 1, padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', color: 'white', border: '1px solid var(--border-color)' }}
            />
            <button className="button primary" onClick={handleCreate}>Add Endpoint</button>
          </div>

          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {endpoints.map(e => (
              <div key={e.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                <div>
                  <strong>{e.url}</strong>
                  <div className="text-muted" style={{ fontSize: '0.85rem' }}>Added {new Date(e.created_at).toLocaleDateString()}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span className="badge neutral">Healthy</span>
                  <button className="button danger" style={{ padding: '0.25rem 0.5rem', fontSize: '0.85rem' }} onClick={() => handleDelete(e.id)}>Delete</button>
                </div>
              </div>
            ))}
            {endpoints.length === 0 && <div className="text-muted">No webhooks configured.</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
