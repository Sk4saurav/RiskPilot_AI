"use client";

import { useState, useEffect } from "react";
import { listApiKeys } from "@/lib/api";

export default function QuickstartPage() {
  const [keys, setKeys] = useState<any[]>([]);
  const [apiKey, setApiKey] = useState("rp_live_XXXXXXXXXXXXXXXX");
  const [loading, setLoading] = useState(true);
  
  const orgId = typeof window !== "undefined" ? localStorage.getItem("org_id") : null;

  useEffect(() => {
    if (orgId) {
      listApiKeys(orgId).then(data => {
        setKeys(data);
        if (data.length > 0 && !data[0].revoked_at) {
          // Just show prefix to indicate they have a key
          setApiKey(data[0].prefix + "...");
        }
        setLoading(false);
      }).catch(err => {
        console.error(err);
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [orgId]);

  return (
    <div className="container">
      <div className="header">
        <h1 className="title">Developer Quickstart</h1>
      </div>

      <div className="glass-panel" style={{ maxWidth: "800px", marginBottom: "2rem" }}>
        <h2>1. Authentication</h2>
        <p className="text-secondary" style={{ marginTop: "0.5rem", marginBottom: "1rem" }}>
          All requests to the RiskPilot API must be authenticated using an API Key. 
          You can generate and revoke API keys from your <a href="/settings" style={{ color: "var(--accent-primary)" }}>Settings</a> page.
        </p>
        <div className="code-block" style={{ marginBottom: "2rem" }}>
          Authorization: Bearer {apiKey}
        </div>

        <h2>2. Ingest an Event</h2>
        <p className="text-secondary" style={{ marginTop: "0.5rem", marginBottom: "1rem" }}>
          Send your customer events to the RiskPilot ingestion endpoint. The system will automatically investigate the event based on your active policy.
        </p>
        
        <div className="form-group">
          <label className="form-label">cURL Example</label>
          <div className="code-block">
{`curl -X POST ${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/v1/events/ingest \\
  -H "Authorization: Bearer ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_id": "evt_123",
    "event_type": "payment.transaction",
    "occurred_at": "${new Date().toISOString()}",
    "source": "my_payment_system",
    "external_id": "txn_18492",
    "subject": {
      "type": "customer",
      "id": "cust_1042"
    },
    "payload": {
      "amount": 1500,
      "ip_address": "192.168.1.100"
    }
  }'`}
          </div>
        </div>

        <h2>3. Retrieve the Risk Assessment</h2>
        <p className="text-secondary" style={{ marginTop: "0.5rem", marginBottom: "1rem" }}>
          The API returns the ingestion status immediately. You can retrieve the generated Risk Case ID from the response and poll for the final Risk Assessment.
        </p>
        <div className="code-block">
{`curl -X GET ${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/v1/cases/<CASE_ID>/assessment \\
  -H "Authorization: Bearer ${apiKey}"`}
        </div>
      </div>
    </div>
  );
}
