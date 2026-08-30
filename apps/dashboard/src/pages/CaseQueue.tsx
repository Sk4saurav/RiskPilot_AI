import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchCases, type Case } from '../api';
import { Search, Filter } from 'lucide-react';

export const CaseQueue = () => {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    try {
      const data = await fetchCases('PENDING_REVIEW');
      setCases(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    const p = priority?.toLowerCase() || 'medium';
    return <span className={`badge ${p}`}>{priority || 'MEDIUM'}</span>;
  };

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 className="page-title" style={{ margin: 0 }}>Case Queue</h1>
        <div style={{ display: 'flex', gap: '12px' }}>
          <div style={{ position: 'relative', width: '250px' }}>
            <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
            <input type="text" className="input-field" placeholder="Search cases..." style={{ paddingLeft: '34px' }} />
          </div>
          <button className="btn btn-outline">
            <Filter size={16} />
            Filter
          </button>
        </div>
      </div>
      
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>CASE ID</th>
              <th>EVENT ID</th>
              <th>SEVERITY</th>
              <th>STATUS</th>
              <th>SLA</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: '32px' }}>Loading cases...</td></tr>
            ) : cases.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-secondary)' }}>No pending cases found.</td></tr>
            ) : (
              cases.map(c => (
                <tr key={c.id} onClick={() => navigate(`/cases/${c.id}`)}>
                  <td style={{ fontWeight: 500 }}>{c.id}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{c.event_id}</td>
                  <td>{getPriorityBadge(c.priority)}</td>
                  <td><span className="badge neutral">{c.status}</span></td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {c.sla_deadline ? new Date(c.sla_deadline).toLocaleTimeString() : 'N/A'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
