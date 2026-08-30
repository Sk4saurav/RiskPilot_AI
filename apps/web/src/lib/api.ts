const API_BASE = "http://localhost:8000/v1";

// Helper to get auth headers for internal user-facing API calls
function getAuthHeaders() {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return {
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
  };
}

// --- Auth ---

export async function signupUser(email: string, password: string, organizationName: string) {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, organization_name: organizationName }),
  });
  if (!res.ok) throw new Error("Failed to sign up");
  return res.json();
}

export async function loginUser(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error("Failed to log in");
  return res.json();
}

// --- Organizations & Onboarding ---

export async function createOrganization(name: string) {
  const res = await fetch(`${API_BASE}/orgs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Failed to create organization");
  return res.json();
}

export async function createApiKey(orgId: string) {
  const res = await fetch(`${API_BASE}/orgs/${orgId}/apikeys`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to create API key");
  return res.json();
}

export async function listApiKeys(orgId: string) {
  const res = await fetch(`${API_BASE}/orgs/${orgId}/apikeys`);
  if (!res.ok) throw new Error("Failed to list API keys");
  return res.json();
}

export async function revokeApiKey(orgId: string, keyId: string) {
  const res = await fetch(`${API_BASE}/orgs/${orgId}/apikeys/${keyId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to revoke API key");
  return res.json();
}

export async function createPolicy(name: string, rulesConfig: any, thresholds: any) {
  const res = await fetch(`${API_BASE}/policies`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      name,
      rules_config: rulesConfig,
      thresholds,
      is_active: true
    }),
  });
  if (!res.ok) throw new Error("Failed to create policy");
  return res.json();
}

export async function ingestEvent(apiKey: string, payload: any) {
  const res = await fetch(`${API_BASE}/events/ingest`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to ingest event");
  return res.json();
}

// --- Cases & Investigations ---

export async function fetchCases() {
  const res = await fetch(`${API_BASE}/cases`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch cases");
  return res.json();
}

export async function fetchCase(id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch case");
  return res.json();
}

export async function fetchCaseTimeline(id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/timeline`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch timeline");
  return res.json();
}

export async function fetchCaseEvidence(id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/evidence`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch evidence");
  return res.json();
}

export async function fetchCaseAssessment(id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/assessment`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch assessment");
  return res.json();
}

export async function askCopilot(id: string, query: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/copilot/ask`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error("Failed to ask copilot");
  return res.json();
}

export async function submitDecision(id: string, decision: string, reason: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/decisions`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      human_decision: decision,
      reason,
      actor_id: "user_analyst_1",
    }),
  });
  if (!res.ok) throw new Error("Failed to submit decision");
  return res.json();
}

export async function fetchCaseNotes(id: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/notes`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch notes");
  return res.json();
}

export async function createCaseNote(id: string, content: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/notes`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error("Failed to create note");
  return res.json();
}

export async function reassignCase(id: string, userId: string) {
  const res = await fetch(`${API_BASE}/cases/${id}/assign?user_id=${userId}`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to reassign case");
  return res.json();
}

export async function createWebhookEndpoint(url: string) {
  const res = await fetch(`${API_BASE}/webhooks/endpoints`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw new Error("Failed to create webhook endpoint");
  return res.json();
}

export async function listWebhookEndpoints() {
  const res = await fetch(`${API_BASE}/webhooks/endpoints`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to list webhook endpoints");
  return res.json();
}

export async function deleteWebhookEndpoint(id: string) {
  const res = await fetch(`${API_BASE}/webhooks/endpoints/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to delete webhook endpoint");
  return res.json();
}

export async function fetchValidationReport() {
  const res = await fetch(`${API_BASE}/cases/validation/report`, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error("Failed to fetch validation report");
  return res.json();
}
