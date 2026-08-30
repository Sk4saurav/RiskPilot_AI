'use client';
import { useEffect, useState } from 'react';
import { fetchValidationReport } from '@/lib/api';

export default function ValidationDashboard() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    try {
      const data = await fetchValidationReport();
      setReport(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="container"><p>Loading validation data...</p></div>;

  if (!report || report.total_replayed === 0) {
    return (
      <div className="container">
        <div className="header">
          <h1 className="title">Alpha 0.6 Validation Scorecard</h1>
        </div>
        <div className="glass-panel text-center">
          <h3>No Validation Data Found</h3>
          <p className="text-secondary">Run the Historical Importer to inject a baseline dataset.</p>
        </div>
      </div>
    );
  }

  const { metrics, total_replayed } = report;

  return (
    <div className="container">
      <div className="header">
        <h1 className="title">Alpha 0.6 Validation Scorecard</h1>
        <p className="text-secondary">Historical Replay Experiment Results</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        
        {/* Core ROI Metric */}
        <div className="glass-panel" style={{ textAlign: 'center', padding: '2rem', background: 'var(--bg-secondary)', border: '2px solid var(--accent-low)' }}>
          <div className="text-secondary" style={{ fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px' }}>Time Saved</div>
          <div style={{ fontSize: '3.5rem', fontWeight: 'bold', color: 'var(--accent-low)', margin: '1rem 0' }}>
            ↓ {metrics.time_saved_pct}%
          </div>
          <div style={{ fontSize: '1.2rem' }}>
            {metrics.time_saved_min_per_case} minutes saved per case
          </div>
        </div>

        {/* Time Breakdown */}
        <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>Time Breakdown</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span className="text-secondary">Manual Baseline Avg</span>
            <strong style={{ color: 'var(--text-muted)' }}>{metrics.manual_baseline_avg_min} min</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span className="text-secondary">RiskPilot Investigation</span>
            <strong style={{ color: 'var(--status-low)' }}>{metrics.riskpilot_inv_avg_min} min</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span className="text-secondary">Analyst Review</span>
            <strong style={{ color: 'var(--status-low)' }}>{metrics.analyst_review_avg_min} min</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
            <strong>RiskPilot Total</strong>
            <strong style={{ color: 'var(--accent-low)' }}>{(metrics.riskpilot_inv_avg_min + metrics.analyst_review_avg_min).toFixed(1)} min</strong>
          </div>
        </div>
      </div>

      {/* KPI Table */}
      <h2 style={{ marginBottom: '1rem' }}>Validation KPIs</h2>
      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--bg-secondary)', textAlign: 'left' }}>
              <th style={{ padding: '1rem' }}>KPI</th>
              <th style={{ padding: '1rem' }}>Result</th>
              <th style={{ padding: '1rem' }}>Target</th>
              <th style={{ padding: '1rem' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '1rem' }}>Cases Replayed</td>
              <td style={{ padding: '1rem', fontWeight: 'bold' }}>{total_replayed}</td>
              <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>&ge; 100</td>
              <td style={{ padding: '1rem' }}>{total_replayed >= 100 ? '🟢' : '🟡'}</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '1rem' }}>Time Saved</td>
              <td style={{ padding: '1rem', fontWeight: 'bold' }}>{metrics.time_saved_pct}%</td>
              <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>&gt; 60%</td>
              <td style={{ padding: '1rem' }}>{metrics.time_saved_pct > 60 ? '🟢' : '🔴'}</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '1rem' }}>False Positive Rate</td>
              <td style={{ padding: '1rem', fontWeight: 'bold' }}>{metrics.false_positive_rate_pct}%</td>
              <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>&le; Baseline</td>
              <td style={{ padding: '1rem' }}>—</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '1rem' }}>Decision Overturn Rate</td>
              <td style={{ padding: '1rem', fontWeight: 'bold' }}>{metrics.decision_overturn_rate_pct}%</td>
              <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>Investigate</td>
              <td style={{ padding: '1rem' }}>—</td>
            </tr>
            <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
              <td style={{ padding: '1rem' }}>Copilot Hallucinations</td>
              <td style={{ padding: '1rem', fontWeight: 'bold' }}>Pending Analyst Review</td>
              <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>0</td>
              <td style={{ padding: '1rem' }}>—</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
