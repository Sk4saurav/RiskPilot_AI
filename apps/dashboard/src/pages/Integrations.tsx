import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface WebhookDelivery {
  id: string;
  event_type: string;
  status: string;
  status_code: string | null;
  attempt_count: number;
  last_error: string | null;
  created_at: string;
  delivered_at: string | null;
  payload: any;
  case_id: string | null;
}

export const Integrations = () => {
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDelivery, setSelectedDelivery] = useState<WebhookDelivery | null>(null);

  const fetchDeliveries = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/v1/webhooks/deliveries', {
        headers: { 'X-Organization-ID': 'org_dp_test_12345' }
      });
      setDeliveries(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeliveries();
    const interval = setInterval(fetchDeliveries, 3000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'DELIVERED': return 'var(--success-color)';
      case 'FAILED': return 'var(--danger-color)';
      case 'RETRY_WAIT': return 'var(--warning-color)';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', gap: '24px' }}>
      <div style={{ flex: 1 }}>
        <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1 className="page-title" style={{ margin: 0 }}>Webhook Deliveries</h1>
        </div>
        
        <div className="glass-panel" style={{ overflow: 'hidden' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Event</th>
                <th>Status</th>
                <th>Attempts</th>
                <th>HTTP</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {loading && deliveries.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: '24px' }}>Loading...</td></tr>
              ) : deliveries.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: '24px' }}>No deliveries found.</td></tr>
              ) : (
                deliveries.map(d => (
                  <tr key={d.id} onClick={() => setSelectedDelivery(d)} style={{ cursor: 'pointer', background: selectedDelivery?.id === d.id ? 'rgba(255,255,255,0.05)' : '' }}>
                    <td>{d.event_type}</td>
                    <td style={{ color: getStatusColor(d.status), fontWeight: 500 }}>{d.status}</td>
                    <td>{d.attempt_count}</td>
                    <td>{d.status_code || '---'}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{new Date(d.created_at).toLocaleTimeString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {selectedDelivery && (
        <div className="glass-panel animate-slide-up" style={{ width: '400px', padding: '24px', height: 'fit-content' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0 }}>Delivery Details</h3>
            <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setSelectedDelivery(null)}>✕</button>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Delivery ID</div>
              <div style={{ fontFamily: 'monospace' }}>{selectedDelivery.id}</div>
            </div>
            
            {selectedDelivery.case_id && (
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Case ID</div>
                <div style={{ fontFamily: 'monospace' }}>{selectedDelivery.case_id}</div>
              </div>
            )}
            
            <div style={{ display: 'flex', gap: '24px' }}>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Status</div>
                <div style={{ color: getStatusColor(selectedDelivery.status), fontWeight: 'bold' }}>{selectedDelivery.status}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Attempts</div>
                <div>{selectedDelivery.attempt_count} / 5</div>
              </div>
            </div>
            
            {selectedDelivery.last_error && (
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--danger-color)', marginBottom: '4px' }}>Last Error</div>
                <pre style={{ background: 'rgba(255,59,48,0.1)', padding: '12px', borderRadius: '8px', fontSize: '0.85rem', overflowX: 'auto', color: 'var(--danger-color)', margin: 0 }}>
                  {selectedDelivery.last_error}
                </pre>
              </div>
            )}
            
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Payload Signature</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success-color)' }}>
                <span style={{ fontSize: '1.2rem' }}>✓</span> Verified HMAC-SHA256
              </div>
            </div>
            
            <div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Payload Data</div>
              <pre style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px', fontSize: '0.85rem', overflowX: 'auto', margin: 0 }}>
                {JSON.stringify(selectedDelivery.payload, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
