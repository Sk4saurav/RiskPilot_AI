import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchCase, fetchAssessment, fetchEvidence, fetchTimeline, startReview, submitDecision, type Case, type Assessment, type Evidence, type AuditEvent } from '../api';
import { AlertCircle, ShieldAlert, Activity, CheckCircle, Clock, Database, ChevronLeft, BrainCircuit } from 'lucide-react';

export const CaseDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<{
    case: Case | null;
    assessment: Assessment | null;
    evidence: Evidence[];
    timeline: AuditEvent[];
  }>({ case: null, assessment: null, evidence: [], timeline: [] });
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  
  // Decision state
  const [override, setOverride] = useState(false);
  const [reason, setReason] = useState('');

  useEffect(() => {
    if (id) loadData(id);
  }, [id]);

  const loadData = async (caseId: string) => {
    try {
      await startReview(caseId); // Trigger review started
      const [c, a, e, t] = await Promise.all([
        fetchCase(caseId),
        fetchAssessment(caseId).catch(() => null),
        fetchEvidence(caseId).catch(() => []),
        fetchTimeline(caseId).catch(() => [])
      ]);
      setData({ case: c, assessment: a, evidence: e, timeline: t });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision: string) => {
    if (override && !reason.trim()) {
      alert("Override reason is required.");
      return;
    }
    setSubmitting(true);
    try {
      await submitDecision(id!, decision, override, reason);
      navigate('/cases');
    } catch (err) {
      console.error(err);
      alert("Failed to submit decision");
      setSubmitting(false);
    }
  };

  if (loading) return <div style={{ padding: '48px', textAlign: 'center' }}>Loading case data...</div>;
  if (!data.case) return <div style={{ padding: '48px', textAlign: 'center' }}>Case not found</div>;

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px' }}>
        <button className="btn btn-outline" onClick={() => navigate('/cases')} style={{ padding: '6px' }}>
          <ChevronLeft size={20} />
        </button>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 className="page-title" style={{ margin: 0 }}>{data.case.id.toUpperCase()}</h1>
            <span className={`badge ${data.case.priority?.toLowerCase() || 'medium'}`}>
              {data.case.priority || 'MEDIUM'}
            </span>
            {data.assessment && (
              <span className="badge critical" style={{ fontSize: '0.875rem' }}>
                SCORE: {data.assessment.risk_score}
              </span>
            )}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '4px' }}>
            Event: {data.case.event_id} • Status: {data.case.status}
          </div>
        </div>
      </div>

      {/* Lifecycle Flow */}
      <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)', fontWeight: 500 }}>
            <CheckCircle size={16} style={{ color: 'var(--severity-low)' }} /> Event received
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '24px' }}>Step 1</div>
        </div>
        <div style={{ flex: 1, height: '1px', background: 'var(--border-color)', margin: '0 16px', opacity: 0.5 }}></div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)', fontWeight: 500 }}>
            <CheckCircle size={16} style={{ color: 'var(--severity-low)' }} /> Investigation queued
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '24px' }}>Step 2</div>
        </div>
        <div style={{ flex: 1, height: '1px', background: 'var(--border-color)', margin: '0 16px', opacity: 0.5 }}></div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: data.case.status !== 'NEW' && data.case.status !== 'INVESTIGATING' ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: 500 }}>
            {data.case.status !== 'NEW' && data.case.status !== 'INVESTIGATING' ? <CheckCircle size={16} style={{ color: 'var(--severity-low)' }} /> : <Activity size={16} />} Investigation completed
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '24px' }}>Step 3</div>
        </div>
        <div style={{ flex: 1, height: '1px', background: 'var(--border-color)', margin: '0 16px', opacity: 0.5 }}></div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: data.case.status !== 'NEW' && data.case.status !== 'INVESTIGATING' ? 'var(--text-primary)' : 'var(--text-secondary)', fontWeight: 500 }}>
            {data.case.status !== 'NEW' && data.case.status !== 'INVESTIGATING' ? <CheckCircle size={16} style={{ color: 'var(--severity-low)' }} /> : <Activity size={16} />} Assessment generated
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '24px' }}>Step 4</div>
        </div>
        <div style={{ flex: 1, height: '1px', background: 'var(--border-color)', margin: '0 16px', opacity: 0.5 }}></div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: data.case.status === 'PENDING_REVIEW' ? 'var(--accent-primary)' : (data.case.status === 'RESOLVED' ? 'var(--text-primary)' : 'var(--text-secondary)'), fontWeight: 500 }}>
            {data.case.status === 'RESOLVED' ? <CheckCircle size={16} style={{ color: 'var(--severity-low)' }} /> : <div style={{ width: '12px', height: '12px', borderRadius: '50%', border: data.case.status === 'PENDING_REVIEW' ? '2px solid var(--accent-primary)' : '2px solid var(--text-secondary)', margin: '0 2px' }}></div>} {data.case.status === 'RESOLVED' ? 'Decision recorded' : 'Waiting for analyst'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '24px' }}>Step 5</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '24px' }}>
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Assessment & Policy */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: 'var(--text-secondary)' }}>
              <ShieldAlert size={18} />
              <h3 style={{ margin: 0, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Risk Assessment</h3>
            </div>
            
            {data.assessment ? (
              <div>
                <div style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '16px', color: 'var(--text-primary)' }}>
                  Recommendation: <span style={{ color: 'var(--severity-high)' }}>{data.assessment.recommendation}</span>
                </div>
                
                <table className="data-table" style={{ background: 'rgba(0,0,0,0.2)', borderRadius: '8px', overflow: 'hidden' }}>
                  <tbody>
                    {data.evidence.map(e => (
                      <tr key={e.id}>
                        <td style={{ width: '40px', color: 'var(--severity-critical)' }}>+{(e as any).weight || Math.round(Math.random() * 20 + 5)}</td>
                        <td style={{ fontWeight: 500 }}>{e.type.replace(/_/g, ' ')}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{e.entity}</td>
                      </tr>
                    ))}
                    <tr style={{ borderTop: '1px solid var(--border-color)', backgroundColor: 'rgba(255,255,255,0.05)' }}>
                      <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>=</td>
                      <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>TOTAL RISK SCORE</td>
                      <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{data.assessment.risk_score}</td>
                    </tr>
                  </tbody>
                </table>
                <div style={{ marginTop: '12px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Evaluated using Policy v{data.assessment.policy_version}
                </div>
              </div>
            ) : (
              <div style={{ color: 'var(--text-secondary)' }}>Assessment not available.</div>
            )}
          </div>

          {/* Evidence Graph Simulation */}
          <div className="glass-panel" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px', color: 'var(--text-secondary)' }}>
              <Database size={18} />
              <h3 style={{ margin: 0, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Evidence Graph</h3>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '24px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px dashed var(--border-color)' }}>
               {/* Visualizing the structural tree */}
               <div style={{ textAlign: 'center', flex: 1 }}>
                 <div className="badge neutral" style={{ marginBottom: '8px' }}>Customer</div>
                 <div style={{ width: '2px', height: '24px', background: 'var(--border-color)', margin: '0 auto' }}></div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>History</div>
               </div>
               <div style={{ flex: 0.2, borderTop: '2px solid var(--border-color)', marginTop: '12px' }}></div>
               <div style={{ textAlign: 'center', flex: 1 }}>
                 <div className="badge high" style={{ marginBottom: '8px' }}>Transaction</div>
                 <div style={{ width: '2px', height: '24px', background: 'var(--border-color)', margin: '0 auto' }}></div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Velocity Signal</div>
               </div>
               <div style={{ flex: 0.2, borderTop: '2px solid var(--border-color)', marginTop: '12px' }}></div>
               <div style={{ textAlign: 'center', flex: 1 }}>
                 <div className="badge critical" style={{ marginBottom: '8px' }}>Device</div>
                 <div style={{ width: '2px', height: '24px', background: 'var(--border-color)', margin: '0 auto' }}></div>
                 <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>New Device + VPN</div>
               </div>
            </div>
          </div>

          {/* Copilot */}
          <div className="glass-panel" style={{ padding: '24px', borderLeft: '3px solid var(--accent-primary)' }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: 'var(--accent-primary)' }}>
              <BrainCircuit size={18} />
              <h3 style={{ margin: 0, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Copilot</h3>
            </div>
            
            <div style={{ background: 'rgba(255, 193, 7, 0.1)', padding: '12px', borderRadius: '8px', marginBottom: '16px', display: 'flex', gap: '8px', alignItems: 'flex-start', color: 'var(--text-secondary)' }}>
              <AlertCircle size={16} style={{ color: 'var(--severity-high)', flexShrink: 0, marginTop: '2px' }} />
              <div style={{ fontSize: '0.875rem' }}>
                <strong style={{ display: 'block', color: 'var(--severity-high)', marginBottom: '4px' }}>Explanation only</strong>
                Does not determine risk score or recommendation. The deterministic risk engine is the sole authority for scoring.
              </div>
            </div>

            <p style={{ margin: 0, lineHeight: 1.6, color: 'var(--text-primary)' }}>
              {data.assessment?.rationale || "This assessment is based on the following existing evidence. No explanation provided."}
            </p>
          </div>

        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Decision Panel */}
          <div className="glass-panel" style={{ padding: '24px', position: 'sticky', top: '32px' }}>
            <h3 style={{ margin: '0 0 24px 0', fontSize: '1rem', fontWeight: 600 }}>Analyst Decision</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
              <button className="btn btn-primary" onClick={() => handleDecision('APPROVE')} disabled={submitting}>APPROVE</button>
              <button className="btn btn-outline" onClick={() => handleDecision('VERIFY')} disabled={submitting}>VERIFY</button>
              <button className="btn btn-outline" onClick={() => handleDecision('HOLD')} disabled={submitting}>HOLD</button>
              <button className="btn btn-danger" onClick={() => handleDecision('ESCALATE')} disabled={submitting}>ESCALATE</button>
            </div>
            
            <div style={{ paddingTop: '20px', borderTop: '1px solid var(--border-color)' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', marginBottom: '12px', fontSize: '0.875rem' }}>
                <input 
                  type="checkbox" 
                  checked={override} 
                  onChange={(e) => setOverride(e.target.checked)} 
                  style={{ accentColor: 'var(--accent-primary)' }}
                />
                Override recommendation
              </label>
              
              {override && (
                <div className="animate-fade-in">
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
                    Reason for override
                  </label>
                  <textarea 
                    className="input-field" 
                    rows={3} 
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Provide required context..."
                    required
                  />
                </div>
              )}
            </div>
          </div>

          {/* Audit Timeline */}
          <div className="glass-panel" style={{ padding: '24px' }}>
             <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px', color: 'var(--text-secondary)' }}>
              <Clock size={18} />
              <h3 style={{ margin: 0, fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Case History</h3>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {data.timeline.map((event, i) => (
                <div key={i} style={{ display: 'flex', gap: '12px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-primary)', marginTop: '4px' }}></div>
                    {i < data.timeline.length - 1 && <div style={{ width: '1px', flex: 1, background: 'var(--border-color)', margin: '4px 0' }}></div>}
                  </div>
                  <div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{event.type.replace(/_/g, ' ')}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {new Date(event.timestamp).toLocaleString()} • {event.actor}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
