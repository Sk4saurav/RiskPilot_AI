import React, { useEffect, useState } from 'react';
import { fetchValidationReport } from '../api';

export const Analytics = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchValidationReport('run_ee937f93ced1')
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="animate-fade-in p-8 text-center" style={{ color: 'var(--text-secondary)' }}>Loading Validation Data...</div>;
  }

  if (!data || data.status === 'no_data') {
    return (
      <div className="animate-fade-in">
        <h1 className="page-title">Validation / Analytics</h1>
        <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          <p>No historical replay data found. Please run the validation script first.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0, marginBottom: '8px' }}>Validation / Analytics</h1>
          <span style={{ 
            background: 'rgba(59, 130, 246, 0.1)', 
            color: '#60A5FA', 
            padding: '4px 12px', 
            borderRadius: '4px', 
            fontSize: '0.85rem',
            fontWeight: 500,
            border: '1px solid rgba(59, 130, 246, 0.2)'
          }}>
            Historical Replay — Synthetic/Design-Partner Dataset
          </span>
        </div>
      </div>

      <div style={{ padding: '16px', background: 'rgba(255, 193, 7, 0.1)', border: '1px solid rgba(255, 193, 7, 0.2)', borderRadius: '8px', marginBottom: '24px', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
        <div style={{ color: '#F59E0B', flexShrink: 0, marginTop: '2px' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        </div>
        <div>
          <div style={{ color: '#F59E0B', fontWeight: 600, marginBottom: '4px' }}>Synthetic Validation Dataset</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', lineHeight: 1.5 }}>
            These metrics represent a 100-case synthetic validation run against a design-partner dataset. Live customer performance was not validated because no external design partner was available during development.
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Cases Replayed
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 600, color: '#F3F4F6' }}>
            {data.cases}
          </div>
        </div>
        
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Time Saved / Case
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 600, color: '#34D399' }}>
            {data.time_saved.absolute_per_case}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Reduction
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 600, color: '#34D399' }}>
            {data.time_saved.relative_percent}%
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Decision Agreement
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 600, color: '#60A5FA' }}>
            {data.risk_quality.decision_agreement_pct}%
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        <div className="glass-panel">
          <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 500, color: '#E5E7EB' }}>Time Breakdown</h3>
          </div>
          <div style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Manual Investigation</span>
              <span style={{ color: '#F3F4F6' }}>{data.manual_baseline.investigation_time}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Manual Review</span>
              <span style={{ color: '#F3F4F6' }}>{data.manual_baseline.analyst_review}</span>
            </div>
            <div style={{ height: '1px', background: 'rgba(255,255,255,0.1)', margin: '16px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>RiskPilot Investigation</span>
              <span style={{ color: '#34D399', fontWeight: 500 }}>{data.riskpilot.investigation_time}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>RiskPilot Review</span>
              <span style={{ color: '#34D399', fontWeight: 500 }}>{data.riskpilot.analyst_review}</span>
            </div>
          </div>
        </div>

        <div className="glass-panel">
          <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 500, color: '#E5E7EB' }}>Quality Metrics</h3>
          </div>
          <div style={{ padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>False Positive Rate</span>
              <span style={{ color: '#F3F4F6' }}>{data.risk_quality.false_positive_rate_pct}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Evidence Coverage</span>
              <span style={{ color: '#F3F4F6' }}>{data.evidence.coverage_pct}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Copilot Hallucinations</span>
              <span style={{ color: '#F3F4F6' }}>{data.copilot.hallucinations}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Decision Overturn Rate</span>
              <span style={{ color: '#F3F4F6' }}>{data.risk_quality.decision_overturn_pct}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
