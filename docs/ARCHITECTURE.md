# RiskPilot Architecture

RiskPilot is built on a fundamental philosophy: **RiskPilot recommends. The analyst decides.**

To satisfy the stringent audit and predictability requirements of enterprise trust & safety teams, RiskPilot rejects the paradigm of "LLM-as-an-Agent" taking autonomous action. Instead, we use a **Deterministic Risk Engine** combined with a bounded, structured **AI Copilot**.

## 1. The Deterministic Risk Engine

The core of RiskPilot (`packages/domain`) is a pure Python, framework-agnostic domain layer. 

### The Evidence Graph
When an `Event` arrives, the `InvestigationWorker` traverses the domain to gather `Evidence` (e.g., velocity checks, IP intelligence, device fingerprinting, behavioral patterns). These are hard facts, retrieved deterministically.

### The Policy Engine
Evidence is evaluated synchronously against the organization's `Policy`. Policies define thresholds, point deductions, and automatic severity mapping.
Because the Policy Engine is deterministic, two identical events with the same historical context will *always* produce the exact same Risk Score.

## 2. The Bounded Copilot

Large Language Models (LLMs) are exceptionally good at summarizing complex relationships, but poor at executing rigid rules without hallucination. 

In RiskPilot, the Copilot has **zero direct access to the database or external APIs**.
Instead, the deterministic engine feeds the Copilot a rigid `Context Window` consisting solely of the gathered Evidence and the resulting Risk Score. The Copilot's only job is to synthesize this data into a human-readable **Investigation Narrative**.

If the evidence says "IP is in London", the Copilot is constrained to that fact. This architecture is what guarantees our **0% Hallucination Rate** regarding the underlying facts of a case.

## 3. The Replay Framework

A risk engine is only as good as its verifiability. 

RiskPilot includes a dedicated `Validation` namespace (`ReplayDataset`, `ReplayRun`, `ValidationResult`). This allows risk teams to upload a CSV of historical events (the "Ground Truth") along with the original manual investigation time and decision.

RiskPilot will replay these events through its engine and output an exact comparison:
- How long did the human take vs. RiskPilot?
- Did RiskPilot's recommendation match the human's final decision?
- What was the false positive rate?

These metrics are exposed natively via the `/v1/metrics/system_status` API and rendered directly onto the primary Analyst Dashboard, proving the platform's ROI continuously.

## 4. Separation of Concerns (The API)

The `apps/api` directory is merely a transport layer (FastAPI). It handles HTTP requests, JWT authentication, and routing. It contains absolutely no core business logic.

This guarantees that RiskPilot can easily be embedded directly into another system, or migrated from FastAPI to GRPC or GraphQL without touching the `packages/domain` risk engine.
