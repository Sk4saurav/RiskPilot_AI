# Security & Compliance

RiskPilot handles highly sensitive financial and behavioral data. Security, isolation, and auditability are treated as first-class primitives throughout the stack.

## 1. Multi-Tenant Data Isolation

RiskPilot is designed from the ground up for multi-tenancy.
Every table in the `packages/domain` schema that contains operational data (Events, Cases, Policies) enforces a strict `organization_id` foreign key. 

The FastAPI routing layer (`apps/api`) utilizes Dependency Injection (`get_current_organization`) to ensure that every single HTTP request is scoped to the Organization associated with the authenticated JWT. Cross-tenant data leakage is fundamentally impossible at the ORM layer.

## 2. Immutable Audit Trails

In a Trust & Safety environment, "who did what, and why?" is the most common question during an escalation.

Every state transition in RiskPilot writes an immutable `AuditTrail` record.
- **System Actions**: When the `InvestigationWorker` generates a Risk Score or triggers a Webhook, the system is recorded as the actor.
- **Human Actions**: When an Analyst reviews a case, their explicit `user_id` is recorded.
- **Overrides**: If an Analyst chooses a decision that differs from RiskPilot's recommendation (e.g., RiskPilot recommends `HOLD`, but the analyst clicks `APPROVE`), an explicit `override_reason` is required and durably logged in the `AuditTrail`.

## 3. Webhook Delivery Guarantees

RiskPilot notifies customer systems via Webhooks when a final decision is reached.
To ensure guaranteed delivery and prevent data loss during network blips, RiskPilot uses an asynchronous retry queue:
- Deliveries are logged to the `webhook_deliveries` table.
- A background worker polls for failed deliveries (`is_successful = False`).
- An exponential backoff strategy is applied (retrying up to 5 times) to ensure the target system eventually receives the decision payload.
- All webhook payloads are signed with `HMAC-SHA256` using the organization's Webhook Secret (`X-RiskPilot-Signature`) to prevent spoofing.

## 4. Stateless AI

To comply with data privacy regulations (GDPR, CCPA) and prevent prompt-injection attacks:
1. The LLM has no access to the database.
2. The LLM cannot trigger actions or webhooks.
3. The LLM is only provided a tightly scoped, JSON-formatted `Context Window` of evidence for summarization.
4. PII is hashed or redacted prior to context generation (Feature Flag).
