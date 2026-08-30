'use client';
import { useEffect, useState, use } from 'react';
import { fetchCase, fetchCaseTimeline, fetchCaseEvidence, fetchCaseAssessment, askCopilot, submitDecision, fetchCaseNotes, createCaseNote, reassignCase } from '@/lib/api';

export default function CaseView({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const id = resolvedParams.id;
  
  const [caseData, setCaseData] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [assessment, setAssessment] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Copilot State
  const [chat, setChat] = useState<{role: string, text: string}[]>([]);
  const [query, setQuery] = useState('');
  const [asking, setAsking] = useState(false);

  // Decision State
  const [decisionReason, setDecisionReason] = useState('');

  // Reassignment State
  const [reassignUserId, setReassignUserId] = useState('');
  
  // Notes State
  const [notes, setNotes] = useState<any[]>([]);
  const [newNote, setNewNote] = useState('');

  useEffect(() => {
    Promise.all([
      fetchCase(id),
      fetchCaseTimeline(id),
      fetchCaseEvidence(id),
      fetchCaseAssessment(id).catch(() => null),
      fetchCaseNotes(id).catch(() => [])
    ]).then(([c, t, e, a, n]) => {
      setCaseData(c);
      setTimeline(t);
      setEvidence(e);
      setAssessment(a);
      setNotes(n);
      setLoading(false);
    });
  }, [id]);

  const handleAsk = async () => {
    if (!query) return;
    const q = query;
    setChat(prev => [...prev, { role: 'user', text: q }]);
    setQuery('');
    setAsking(true);
    try {
      const res = await askCopilot(id, q);
      setChat(prev => [...prev, { role: 'ai', text: res.response }]);
    } catch (e) {
      setChat(prev => [...prev, { role: 'ai', text: "Error connecting to AI Copilot." }]);
    }
    setAsking(false);
  };

  const handleDecision = async (decisionType: string) => {
    if (!decisionReason) {
      alert("Please provide a reason for your decision.");
      return;
    }
    try {
      await submitDecision(id, decisionType, decisionReason);
      alert(`Decision ${decisionType} submitted successfully.`);
      window.location.reload();
    } catch (e) {
      alert("Failed to submit decision.");
    }
  };

  const handleAddNote = async () => {
    if (!newNote) return;
    try {
      const note = await createCaseNote(id, newNote);
      setNotes(prev => [...prev, note]);
      setNewNote('');
    } catch (e) {
      alert("Failed to add note.");
    }
  };

  const handleReassign = async () => {
    if (!reassignUserId) return;
    try {
      await reassignCase(id, reassignUserId);
      alert("Case reassigned successfully.");
      setCaseData((prev: any) => ({ ...prev, assigned_to: reassignUserId }));
      setReassignUserId('');
    } catch (e) {
      alert("Failed to reassign case.");
    }
  };

  if (loading) return <div className="container"><p>Loading case...</p></div>;

  const scoreClass = assessment ? 
    (assessment.risk_score >= 80 ? 'critical' : assessment.risk_score >= 60 ? 'high' : assessment.risk_score >= 40 ? 'medium' : 'low') 
    : 'neutral';

  return (
    <div className="container">
      <div className="flex-between">
        <div>
          <h1 className="title" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            CASE {id} 
            <span className={`badge ${caseData.status === 'PENDING_REVIEW' ? 'critical' : 'neutral'}`}>{caseData.status}</span>
          </h1>
          <p className="text-secondary">
            Policy Version: {assessment?.policy_version || 'N/A'} | 
            Assigned to: <strong>{caseData.assigned_to || 'Unassigned'}</strong>
          </p>
          <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
            <input 
              type="text" 
              placeholder="User ID..." 
              value={reassignUserId} 
              onChange={e => setReassignUserId(e.target.value)}
              style={{ padding: '0.25rem 0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'white' }}
            />
            <button className="button" style={{ padding: '0.25rem 0.75rem', fontSize: '0.85rem' }} onClick={handleReassign}>Reassign</button>
          </div>
        </div>
        {assessment && (
          <div className="glass-panel" style={{ textAlign: 'center', minWidth: '150px' }}>
            <div className="text-secondary" style={{ fontSize: '0.875rem', fontWeight: 600 }}>RISK SCORE</div>
            <div className={`score-display ${scoreClass}`}>{assessment.risk_score}</div>
            <div className={`badge ${scoreClass}`}>{assessment.recommendation}</div>
          </div>
        )}
      </div>

      <div className="case-grid">
        {/* Main Content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          <div className="glass-panel">
            <h3 style={{ marginBottom: '1rem' }}>Evidence Graph</h3>
            <div className="evidence-list">
              {evidence.map(e => (
                <div key={e.id} className="evidence-item">
                  <div>
                    <strong>{e.type}</strong>
                    <div className="text-muted">Source: {e.source}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: e.weight > 15 ? 'var(--status-critical)' : 'var(--text-secondary)' }}>+{e.weight} pts</div>
                    <span className={`badge ${e.severity === 'HIGH' ? 'critical' : e.severity === 'MEDIUM' ? 'high' : 'neutral'}`}>
                      {e.severity}
                    </span>
                  </div>
                </div>
              ))}
              {evidence.length === 0 && <p className="text-muted">No evidence found.</p>}
            </div>
          </div>

          <div className="glass-panel">
            <h3 style={{ marginBottom: '1rem' }}>Internal Notes</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1rem', maxHeight: '200px', overflowY: 'auto' }}>
              {notes.map(n => (
                <div key={n.id} style={{ padding: '0.75rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.85rem' }}>
                    <strong>{n.author_id}</strong>
                    <span className="text-muted">{new Date(n.created_at).toLocaleString()}</span>
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{n.content}</div>
                </div>
              ))}
              {notes.length === 0 && <p className="text-muted">No internal notes.</p>}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <textarea 
                placeholder="Add an internal note..."
                value={newNote}
                onChange={e => setNewNote(e.target.value)}
                style={{ flex: 1, minHeight: '40px', padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', color: 'white', border: '1px solid var(--border-color)' }}
              />
              <button className="button primary" onClick={handleAddNote}>Post</button>
            </div>
          </div>

          <div className="glass-panel">
            <h3 style={{ marginBottom: '1rem' }}>Analyst Decision</h3>
            {caseData.status === 'RESOLVED' || caseData.status === 'ESCALATED' ? (
               <p className="text-secondary">Case has been closed.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <textarea 
                  placeholder="Reason for decision..." 
                  value={decisionReason}
                  onChange={e => setDecisionReason(e.target.value)}
                  style={{ width: '100%', minHeight: '80px', padding: '0.75rem', borderRadius: 'var(--radius-md)', background: 'var(--bg-secondary)', color: 'white', border: '1px solid var(--border-color)' }}
                />
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="button" style={{ borderColor: 'var(--status-low)', color: 'var(--status-low)' }} onClick={() => handleDecision('APPROVE')}>Approve</button>
                  <button className="button" style={{ borderColor: 'var(--status-medium)', color: 'var(--status-medium)' }} onClick={() => handleDecision('VERIFY')}>Verify</button>
                  <button className="button" style={{ borderColor: 'var(--status-high)', color: 'var(--status-high)' }} onClick={() => handleDecision('ESCALATE')}>Escalate</button>
                  <button className="button danger" onClick={() => handleDecision('HOLD')}>Hold</button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="glass-panel chat-container">
            <h3 style={{ marginBottom: '1rem' }}>AI Copilot</h3>
            <div className="chat-history">
              {chat.map((msg, i) => (
                <div key={i} className={`chat-bubble ${msg.role}`}>
                  {msg.text}
                </div>
              ))}
              {asking && <div className="chat-bubble ai">Thinking...</div>}
              {chat.length === 0 && <p className="text-muted">Ask anything about this case...</p>}
            </div>
            <div className="chat-input">
              <input 
                type="text" 
                placeholder="Ask a question..." 
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAsk()}
              />
              <button className="button primary" onClick={handleAsk} disabled={asking}>Ask</button>
            </div>
          </div>
          
          <div className="glass-panel">
            <h3 style={{ marginBottom: '1rem' }}>Audit Timeline</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {timeline.map((t, i) => (
                <div key={i} style={{ fontSize: '0.85rem', borderLeft: '2px solid var(--border-color)', paddingLeft: '0.75rem', paddingBottom: '0.5rem' }}>
                  <div className="text-secondary">{new Date(t.timestamp).toLocaleTimeString()}</div>
                  <div><strong>{t.type}</strong></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
