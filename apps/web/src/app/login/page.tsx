"use client";

import { useState } from "react";
import { loginUser } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const res = await loginUser(email, password);
      
      // Store token and org id
      localStorage.setItem("token", res.access_token);
      localStorage.setItem("org_id", res.org_id);
      
      window.location.href = "/";
    } catch (err: any) {
      setError(err.message || "Failed to log in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: "400px", marginTop: "4rem" }}>
      <div className="glass-panel">
        <h1 className="title" style={{ marginBottom: "1.5rem", textAlign: "center" }}>RiskPilot Login</h1>
        
        {error && (
          <div style={{ background: "rgba(239,68,68,0.2)", color: "#fca5a5", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem" }}>
            {error}
          </div>
        )}

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input 
              type="email" 
              className="form-input" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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
            {loading ? "Logging in..." : "Log In"}
          </button>
        </form>

        <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
          <a href="/signup" style={{ color: "var(--accent-primary)", fontSize: "0.875rem" }}>Don't have an account? Sign up</a>
        </div>
      </div>
    </div>
  );
}
