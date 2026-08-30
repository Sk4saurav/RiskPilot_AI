import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle, Database, Server, BrainCircuit, Webhook, Zap, ShieldAlert, Cpu } from 'lucide-react';

export const SystemStatus = () => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate a brief health check loading
    const timer = setTimeout(() => {
      setLoading(false);
    }, 800);
    return () => clearTimeout(timer);
  }, []);

  const services = [
    { name: 'API Server', description: 'FastAPI HTTP transport layer', icon: Server, status: 'Operational', optional: false },
    { name: 'Investigation Worker', description: 'Asynchronous event processor', icon: Activity, status: 'Operational', optional: false },
    { name: 'Database', description: 'PostgreSQL relational store', icon: Database, status: 'Connected', optional: false },
    { name: 'Policy Engine', description: 'Deterministic rule evaluation', icon: ShieldAlert, status: 'Operational', optional: false },
    { name: 'Replay Engine', description: 'Historical validation runner', icon: Cpu, status: 'Operational', optional: false },
    { name: 'Webhook Service', description: 'Decision event propagation', icon: Webhook, status: 'Operational', optional: false },
    { name: 'Copilot', description: 'OpenAI dynamic explanation', icon: BrainCircuit, status: 'Operational', optional: true },
  ];

  if (loading) {
    return <div className="animate-fade-in p-8 text-center" style={{ color: 'var(--text-secondary)' }}>Running health checks...</div>;
  }

  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: '32px' }}>
        <h1 className="page-title" style={{ margin: 0, marginBottom: '8px' }}>System Status</h1>
        <p style={{ color: 'var(--text-secondary)', margin: 0 }}>Current operational status of all RiskPilot core systems and integrations.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '20px' }}>
        {services.map((service, index) => {
          const Icon = service.icon;
          return (
            <div key={index} className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px' }}>
                  <Icon size={24} style={{ color: 'var(--text-primary)' }} />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 500 }}>{service.name}</h3>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '4px' }}>
                    {service.description}
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'flex-end', color: '#34D399', fontWeight: 500 }}>
                  <CheckCircle size={16} /> {service.status}
                </div>
                {service.optional && (
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Optional
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
