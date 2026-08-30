# RiskPilot

## What is RiskPilot?
Fraud and risk analysts spend significant time manually gathering evidence across multiple systems before making a decision. 
RiskPilot automatically gathers and correlates investigation evidence, applies deterministic risk scoring and policy rules, and presents the result to a human analyst.
*RiskPilot recommends. The analyst decides.*

## Architecture
RiskPilot employs an asynchronous, event-driven architecture designed to decouple fast ingestion from slow investigation:

1. **Ingestion**: The API receives a transaction payload and instantly queues an event, returning `200 OK`.
2. **Investigation**: A background worker picks up the event, gathers network/device/identity evidence via Intelligence Adapters.
3. **Assessment**: A deterministic Risk Engine calculates a normalized score (0-100).
4. **Policy**: A rule engine enforces decisions based on the score and evidence, transitioning the case to `PENDING_REVIEW`.
5. **Human Review**: The analyst reviews the correlated evidence and makes a final `APPROVE` or `REJECT` decision.

## Key Design Principles
- **Event-Driven Resilience**: Investigations are executed via robust background polling workers, not ephemeral API threads.
- **Idempotency**: Duplicate event IDs are safely ignored, returning the existing case ID.
- **Deterministic Core**: The risk engine and policy rules are 100% deterministic, ensuring historical replays never drift.
- **AI as an Assistant, Not an Authority**: The LLM Copilot explains evidence but is strictly isolated from the risk scoring mechanism.

## Technology Stack
- **Backend API**: Python, FastAPI
- **Background Worker**: Python, AsyncIO
- **Database**: PostgreSQL (via SQLAlchemy)
- **Frontend Dashboard**: React, Vite, TypeScript
- **Intelligence**: IP-API (Live), Deterministic Mocks (Replay)
- **AI**: OpenAI (Optional Copilot)

## Quick Start
To launch the entire application (API, Worker, Dashboard) in one command:
```powershell
.\scripts\start-demo.ps1
```

## Environment Variables
Copy `.env.example` to `.env`:
```
DATABASE_URL=postgresql+asyncpg://...
RISKPILOT_JWT_SECRET=your_secret

# Optional: Set this to enable the AI Copilot. 
# If not set, the core risk engine remains 100% operational.
OPENAI_API_KEY=sk-... 
```

## Start Backend
If starting manually:
```bash
python -m uvicorn apps.api.app.main:app --reload
```

## Start Worker
If starting manually (requires API & DB to be running):
```bash
python -m workers.investigation.main
```

## Start Dashboard
If starting manually:
```bash
cd apps/dashboard
npm install
npm run dev
```

## Run Customer Simulator
To simulate a live integration event:
```bash
# Obtain your API key by running `python -m tools.demo.reset_demo`
set RISKPILOT_API_KEY=eyJhbGciOiJI...

python -m tools.customer_simulator.main --scenario critical --api-key $env:RISKPILOT_API_KEY
```

## Run Historical Replay
To run the deterministic backtest engine against the synthetic dataset:
```bash
python -m tools.historical-importer.run_experiment
```

## View Validation Results
After running the historical replay, navigate to `http://localhost:5173/analytics` to view the comprehensive time-savings and accuracy metrics.

## Run Tests
Run the evaluator smoke tests to verify complete end-to-end functionality:
```bash
python -m tools.evaluator.smoke_test
```

## Failure Scenario Tests
Run the failure test suite to verify resilience against invalid payloads and unauthorized access:
```bash
python -m tools.evaluator.failure_tests
```

## Security Model
- **Tenant Isolation**: All database queries are explicitly filtered by `organization_id` derived securely from the JWT.
- **Least Privilege**: The Copilot only has read access to evidence and cannot modify risk scores or execute policies.

## Deterministic Risk Engine
The risk engine uses a combination of explicit static weights and dynamic velocity tracking (time-based features) to calculate a consistent score. This allows the system to guarantee reproducibility during validation.

## Copilot Architecture
Copilot is an optional AI layer designed to read the completed evidence graph and synthesize it into a human-readable narrative. If the `OPENAI_API_KEY` is not provided, the Copilot gracefully degrades and is marked as "Unavailable" while the core deterministic engine proceeds uninterrupted.

## Limitations
**The 100-case validation represents synthetic/historical replay validation. Live customer performance was not validated because no external design partner was available.** The historical replay demonstrated a 96.1% reduction in review time (25.8 min manual → 1.0 min RiskPilot) in the synthetic replay environment.
