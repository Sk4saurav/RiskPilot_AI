"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { 
  createOrganization, 
  createPolicy, 
  createApiKey, 
  ingestEvent 
} from "@/lib/api";

const STEPS = [
  "Policy",
  "API Key",
  "Test Event"
];

const DEFAULT_RULES = {
  "HIGH_AMOUNT": 20,
  "VPN_USED": 25,
  "NEW_DEVICE": 15,
  "MULTIPLE_FAILURES": 30
};

const DEFAULT_THRESHOLDS = {
  "LOW": [0, 29],
  "MEDIUM": [30, 59],
  "HIGH": [60, 79],
  "CRITICAL": [80, 100]
};

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [orgName, setOrgName] = useState("");
  const [orgId, setOrgId] = useState<string | null>(null);
  
  const [policyName, setPolicyName] = useState("Default Fraud Policy");
  
  const [apiKey, setApiKey] = useState<{ id: string, key: string, prefix: string } | null>(null);

  // Check if already onboarded (for simple alpha)
  useEffect(() => {
    const existingOrgId = localStorage.getItem("org_id");
    if (existingOrgId && step === 0) {
      // If they somehow got here but already have an org, maybe we let them through or redirect
      // For testing, let's just keep it simple.
    }
  }, [step]);

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const org = await createOrganization(orgName);
      setOrgId(org.id);
      localStorage.setItem("org_id", org.id); // Save for subsequent API calls
      setStep(1);
    } catch (err: any) {
      setError(err.message || "Failed to create organization");
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await createPolicy(policyName, DEFAULT_RULES, DEFAULT_THRESHOLDS);
      setStep(2);
    } catch (err: any) {
      setError(err.message || "Failed to create policy");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateKey = async () => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    try {
      const keyData = await createApiKey(orgId);
      setApiKey(keyData);
      setStep(3);
    } catch (err: any) {
      setError(err.message || "Failed to generate API key");
    } finally {
      setLoading(false);
    }
  };

  const handleTestEvent = async () => {
    if (!apiKey) return;
    setLoading(true);
    setError(null);
    try {
      const testPayload = {
        event_id: `evt_test_${Date.now()}`,
        source: "onboarding_wizard",
        external_id: `tx_${Date.now()}`,
        event_type: "transaction",
        occurred_at: new Date().toISOString(),
        subject: { type: "user", id: "user_test_123" },
        payload: {
          amount: 8500,
          ip: "192.168.1.1",
          device_id: "new_device_99"
        }
      };
      await ingestEvent(apiKey.key, testPayload);
      router.push("/"); // Redirect to dashboard to see the case
    } catch (err: any) {
      setError(err.message || "Failed to trigger event");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="glass-panel wizard-container">
        <h1 className="title" style={{ textAlign: "center", marginBottom: "2rem" }}>
          Welcome to RiskPilot
        </h1>
        
        {/* Wizard Progress */}
        <div className="wizard-steps">
          {STEPS.map((s, idx) => (
            <div 
              key={s} 
              className={`wizard-step-indicator ${step === idx ? 'active' : ''} ${step > idx ? 'completed' : ''}`}
              title={s}
            >
              {step > idx ? "✓" : idx + 1}
            </div>
          ))}
        </div>

        {error && (
          <div style={{ background: "rgba(239,68,68,0.2)", color: "#fca5a5", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
            {error}
          </div>
        )}

        {/* Step 1: Policy */}
        {step === 0 && (
          <form onSubmit={handleCreatePolicy}>
            <h2 style={{ marginBottom: "1rem" }}>Configure Default Policy</h2>
            <p className="text-secondary" style={{ marginBottom: "1.5rem" }}>
              RiskPilot uses policies to evaluate events. We've prepared a default policy for you.
            </p>
            
            <div className="form-group">
              <label className="form-label">Policy Name</label>
              <input 
                type="text" 
                className="form-input" 
                value={policyName} 
                onChange={(e) => setPolicyName(e.target.value)} 
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Risk Signals (Weights)</label>
              <div className="code-block">
                {JSON.stringify(DEFAULT_RULES, null, 2)}
              </div>
            </div>

            <button type="submit" className="button primary" style={{ width: "100%" }} disabled={loading}>
              {loading ? "Saving..." : "Create Policy"}
            </button>
          </form>
        )}

        {/* Step 2: API Key */}
        {step === 1 && (
          <div>
            <h2 style={{ marginBottom: "1rem" }}>Generate API Key</h2>
            <p className="text-secondary" style={{ marginBottom: "1.5rem" }}>
              You'll need an API key to securely send events from your application to RiskPilot.
            </p>
            
            {!apiKey ? (
               <button onClick={handleGenerateKey} className="button primary" style={{ width: "100%" }} disabled={loading}>
                 {loading ? "Generating..." : "Generate Production Key"}
               </button>
            ) : (
               <div>
                 <div className="api-key-box">
                   <div style={{ marginBottom: "0.5rem", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                     Please copy this key now. You won't be able to see it again!
                   </div>
                   <div className="api-key-value">{apiKey.key}</div>
                 </div>
                 <button onClick={() => setStep(2)} className="button primary" style={{ width: "100%" }}>
                   I have copied my key
                 </button>
               </div>
            )}
          </div>
        )}

        {/* Step 3: Test Event */}
        {step === 2 && apiKey && (
          <div>
            <h2 style={{ marginBottom: "1rem" }}>Send a Test Event</h2>
            <p className="text-secondary" style={{ marginBottom: "1.5rem" }}>
              Your RiskPilot infrastructure is ready. Let's send a simulated transaction event to see the worker pipeline in action.
            </p>
            
            <div className="form-group">
              <label className="form-label">cURL Example</label>
              <div className="code-block">
{`curl -X POST http://localhost:8000/v1/events/ingest \\
  -H "Authorization: Bearer ${apiKey.key}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_id": "evt_demo_1",
    "source": "payment_gateway",
    "external_id": "tx_demo_1",
    "event_type": "transaction",
    "occurred_at": "${new Date().toISOString()}",
    "subject": { "type": "user", "id": "u_123" },
    "payload": { "amount": 8500, "ip": "192.168.1.1" }
  }'`}
              </div>
            </div>

            <button onClick={handleTestEvent} className="button primary" style={{ width: "100%" }} disabled={loading}>
              {loading ? "Sending Event..." : "Send Test Event & Go to Dashboard"}
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
