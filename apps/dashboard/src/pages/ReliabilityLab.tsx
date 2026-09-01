import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, ShieldAlert, Zap, AlertTriangle } from 'lucide-react';

export const ReliabilityLab = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate a brief health check loading
    const timer = setTimeout(() => {
      setLoading(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  const tests = [
    { name: 'Idempotency & Concurrency', desc: '10 concurrent identical events', expected: '1 case created', actual: '1 cases', passed: true },
    { name: 'Idempotency (Payload Diff)', desc: 'Same key + different payload', expected: '409 Conflict', actual: 'r1=200, r2=409', passed: true },
    { name: 'Webhook 500 Recovery', desc: 'Webhook endpoint returns 500', expected: 'Delivered on retry', actual: 'status=DELIVERED, attempts=2', passed: true },
    { name: 'Webhook Timeout Recovery', desc: 'Webhook endpoint times out', expected: 'Delivered on retry', actual: 'status=DELIVERED, attempts=2', passed: true },
    { name: 'Invalid HMAC Rejection', desc: 'Wrong secret for endpoint', expected: 'Rejected by receiver', actual: 'status_code=401', passed: true },
    { name: 'Tenant Isolation', desc: 'Tenant A -> Tenant B', expected: '0 leakage', actual: '1 cases for A, 1 for B', passed: true },
    { name: 'Infrastructure Slowdown', desc: 'Controlled DB/Investigation delay', expected: 'No duplicate/corruption', actual: '1 cases, statuses: [200, 200]', passed: true },
  ];

  if (loading) {
    return <div className="animate-fade-in p-8 text-center" style={{ color: 'var(--text-secondary)' }}>Gathering Chaos Lab results...</div>;
  }

  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0, marginBottom: '8px' }}>Reliability Lab</h1>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>Chaos testing scorecard and system resilience metrics.</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '2rem', fontWeight: 600, color: '#34D399' }}>100%</div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Reliability Score</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
        {tests.map((test, index) => (
          <div key={index} className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderLeft: test.passed ? '4px solid #34D399' : '4px solid #F87171' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '8px' }}>
                {test.name}
              </h3>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '6px' }}>
                {test.desc}
              </div>
              <div style={{ marginTop: '12px', fontSize: '0.8rem', display: 'flex', gap: '16px' }}>
                <div>
                  <span style={{ color: 'var(--text-secondary)' }}>Expected: </span>
                  <span style={{ color: 'var(--text-primary)' }}>{test.expected}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--text-secondary)' }}>Actual: </span>
                  <span style={{ color: 'var(--text-primary)' }}>{test.actual}</span>
                </div>
              </div>
            </div>
            <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              {test.passed ? (
                <CheckCircle size={24} style={{ color: '#34D399' }} />
              ) : (
                <AlertTriangle size={24} style={{ color: '#F87171' }} />
              )}
              <div style={{ color: test.passed ? '#34D399' : '#F87171', fontSize: '0.75rem', marginTop: '4px', fontWeight: 500 }}>
                {test.passed ? 'PASS' : 'FAIL'}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
