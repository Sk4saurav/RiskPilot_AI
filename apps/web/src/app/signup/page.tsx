"use client";

import { useState } from "react";
import { signupUser } from "@/lib/api";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await signupUser(email, password, organizationName);
      
      // Store token and org id
      localStorage.setItem("token", res.access_token);
      localStorage.setItem("org_id", res.org_id);
      
      window.location.href = "/";
    } catch (err: any) {
      setError(err.message || "Failed to sign up");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: "400px", marginTop: "4rem" }}>
      <div className="glass-panel">
        <h1 className="title" style={{ marginBottom: "1.5rem", textAlign: "center" }}>Create Organization</h1>
        
        {error && (
          <div style={{ background: "rgba(239,68,68,0.2)", color: "#fca5a5", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSignup}>
          <div className="form-group">
            <label className="form-label">Organization Name</label>
            <input 
              type="text" 
              className="form-input" 
              value={organizationName}
              onChange={(e) => setOrganizationName(e.target.value)}
              placeholder="e.g. Acme Corp"
              required 
            />
          </div>

          <div className="form-group">
            <label className="form-label">Work Email</label>
            <input 
              type="email" 
              className="form-input" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jane@acme.com"
              required 
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Password</label>
            <input 
              type="password" 
              className="form-input" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
          </div>

          <button type="submit" className="button primary" style={{ width: "100%", marginTop: "1rem" }} disabled={loading}>
            {loading ? "Creating Account..." : "Create Account"}
          </button>
        </form>

        <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
          <a href="/login" style={{ color: "var(--accent-primary)", fontSize: "0.875rem" }}>Already have an account? Log in</a>
        </div>
      </div>
    </div>
  );
}
