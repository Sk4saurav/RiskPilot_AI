import axios from 'axios';

const API_URL = import.meta.env.VITE_RISKPILOT_API_URL || 'http://localhost:8000';
const API_TOKEN = import.meta.env.VITE_RISKPILOT_API_TOKEN;

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    ...(API_TOKEN ? { 'Authorization': `Bearer ${API_TOKEN}` } : {})
  }
});

console.log('API_URL:', API_URL);
console.log('API_TOKEN (first 10 chars):', API_TOKEN ? API_TOKEN.substring(0, 10) : 'MISSING');


export interface Case {
  id: string;
  event_id: string;
  status: string;
  priority: string;
  created_at: string;
  sla_deadline?: string;
}

export interface Assessment {
  id: string;
  risk_score: number;
  recommendation: string;
  rationale: string;
  policy_version: number;
  created_at: string;
}

export interface Evidence {
  id: string;
  type: string;
  entity: string;
  severity: string;
  confidence: number;
  explanation: string;
  created_at: string;
}

export interface AuditEvent {
  type: string;
  timestamp: string;
  actor: string;
  metadata: any;
}

export const fetchCases = async (status?: string): Promise<Case[]> => {
  const params = status ? { status } : {};
  const { data } = await api.get('/v1/cases', { params });
  return data;
};

export const fetchCase = async (id: string): Promise<Case> => {
  const { data } = await api.get(`/v1/cases/${id}`);
  return data;
};

export const fetchAssessment = async (id: string): Promise<Assessment> => {
  const { data } = await api.get(`/v1/cases/${id}/assessment`);
  return data;
};

export const fetchEvidence = async (id: string): Promise<Evidence[]> => {
  const { data } = await api.get(`/v1/cases/${id}/evidence`);
  return data;
};

export const fetchTimeline = async (id: string): Promise<AuditEvent[]> => {
  const { data } = await api.get(`/v1/cases/${id}/timeline`);
  return data;
};

export const startReview = async (id: string): Promise<void> => {
  await api.post(`/v1/cases/${id}/start_review`);
};

export const submitDecision = async (
  id: string, 
  decision: string, 
  isOverride: boolean, 
  reason: string
): Promise<void> => {
  await api.post(`/v1/cases/${id}/decisions`, {
    actor_id: 'user_analyst_1',
    analyst_decision: decision,
    is_override: isOverride,
    override_reason: reason,
    missing_evidence: []
  });
};

export const fetchValidationReport = async (runId: string): Promise<any> => {
  const { data } = await api.get(`/v1/validation/runs/${runId}/report`);
  return data;
};

export const fetchSystemStatus = async (): Promise<any> => {
  const { data } = await api.get(`/v1/metrics/system_status`);
  return data;
};
