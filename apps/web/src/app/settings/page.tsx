"use client";

import { useState, useEffect } from "react";
import { createApiKey, listApiKeys, revokeApiKey } from "@/lib/api";

type ApiKey = {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  revoked_at: string | null;
};

export default function SettingsPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [newKey, setNewKey] = useState<{ key: string, prefix: string } | null>(null);

  const orgId = typeof window !== "undefined" ? localStorage.getItem("org_id") : null;

  useEffect(() => {
    if (orgId) {
      loadKeys();
    } else {
      setError("No organization found. Please complete onboarding first.");
      setLoading(false);
    }
  }, [orgId]);

  const loadKeys = async () => {
    if (!orgId) return;
    try {
      setLoading(true);
      const data = await listApiKeys(orgId);
      setKeys(data);
    } catch (err: any) {
      setError(err.message || "Failed to load API keys");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateKey = async () => {
    if (!orgId) return;
    try {
      setLoading(true);
      const keyData = await createApiKey(orgId);
      setNewKey(keyData);
      await loadKeys();
    } catch (err: any) {
      setError(err.message || "Failed to generate key");
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!orgId) return;
    if (!confirm("Are you sure you want to revoke this key? Events using this key will be rejected immediately.")) {
      return;
    }
    
    try {
      setLoading(true);
      await revokeApiKey(orgId, keyId);
      await loadKeys();
    } catch (err: any) {
      setError(err.message || "Failed to revoke key");
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1 className="title">Organization Settings</h1>
      </div>

      {error && (
        <div style={{ background: "rgba(239,68,68,0.2)", color: "#fca5a5", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
          {error}
        </div>
      )}

      <div className="case-grid" style={{ gridTemplateColumns: "1fr" }}>
        
        <div className="glass-panel">
          <div className="flex-between" style={{ marginBottom: "1.5rem" }}>
            <h2>API Keys</h2>
            <button className="button primary" onClick={handleGenerateKey} disabled={loading || !orgId}>
              + Generate New Key
            </button>
          </div>
          
          <p className="text-secondary" style={{ marginBottom: "1.5rem" }}>
            API keys are used to authenticate requests from your external systems to RiskPilot.
          </p>

          {newKey && (
             <div className="api-key-box" style={{ marginBottom: "2rem" }}>
               <div style={{ marginBottom: "0.5rem", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                 New API Key generated! Copy this now. You won't be able to see it again.
               </div>
               <div className="api-key-value">{newKey.key}</div>
               <button className="button" style={{ marginTop: "1rem" }} onClick={() => setNewKey(null)}>
                 Done
               </button>
             </div>
          )}

          {loading && !keys.length && <div>Loading keys...</div>}

          {!loading && keys.length === 0 && (
            <div className="text-muted" style={{ padding: "2rem", textAlign: "center", border: "1px dashed var(--border-color)", borderRadius: "var(--radius-md)" }}>
              No API keys found.
            </div>
          )}

          {keys.length > 0 && (
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Prefix</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {keys.map((k) => (
                  <tr key={k.id}>
                    <td>{k.name}</td>
                    <td style={{ fontFamily: "monospace", color: "var(--text-secondary)" }}>{k.prefix}...</td>
                    <td>{new Date(k.created_at).toLocaleDateString()}</td>
                    <td>
                      {k.revoked_at ? (
                        <span className="badge critical">Revoked</span>
                      ) : (
                        <span className="badge low">Active</span>
                      )}
                    </td>
                    <td>
                      {!k.revoked_at && (
                        <button 
                          className="button danger" 
                          style={{ padding: "0.25rem 0.5rem", fontSize: "0.75rem" }}
                          onClick={() => handleRevokeKey(k.id)}
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
