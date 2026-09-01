# RiskPilot Evaluation Guide

Welcome to the RiskPilot prototype. RiskPilot is an independently testable payment-risk infrastructure demonstrating deterministic risk assessment, concurrency-safe idempotency, reliable webhook delivery, UPI abuse detection, and tenant isolation. 

This guide serves as a map to evaluate the core engineering claims of the system.

## 1. Golden Path Demonstration

To witness the entire lifecycle of an event—from ingestion to analyst dashboard to webhook dispatch—execute the deterministic "Golden Demo":

1. Open PowerShell and start the local infrastructure:
   ```powershell
   .\start-demo.ps1
   ```
2. In a new PowerShell window, run the evaluation script:
   ```powershell
   .\run-evaluation.ps1
   ```
3. Navigate to the **Dashboard** (`http://localhost:5173`) to view the newly created Risk Case, explore the Evidence Graph (+25 UPI Abuse Ring signal), and review the Reliability Lab scorecard.

## 2. Claim Verification

We make specific engineering claims about RiskPilot's architecture. Use the commands below to verify them independently.

### Claim 1: Concurrency-Safe Idempotency
**Claim:** The system can handle rapid bursts of exact duplicate events without causing database `IntegrityError` collisions or creating duplicate cases. 
**Verification:**
```powershell
python tools/evaluator/test_chaos_lab.py
```
**Expected:** Sends 10 identical events concurrently. 1 is processed (200), 9 are rejected (202), exactly 1 risk case is created.

### Claim 2: Reliable Webhook Delivery (Exponential Backoff)
**Claim:** Outbound webhooks are managed via an outbox state machine. If the receiving endpoint times out or returns HTTP 500, the system automatically retries with exponential backoff until successful.
**Verification:**
```powershell
python tools/evaluator/test_chaos_lab.py
# Check the "Webhook 500 Recovery" and "Webhook timeout Recovery" outputs
```
**Expected:** The webhook dispatcher transitions from `RETRY_WAIT` to `DELIVERED` on attempt > 1.

### Claim 3: Tenant Isolation (Zero Leakage)
**Claim:** Strict contextual boundaries ensure that Tenant A cannot pollute Tenant B's risk investigations, event history, or webhook payloads.
**Verification:**
```powershell
python tools/evaluator/test_chaos_lab.py
```
**Expected:** Tenant A and Tenant B ingest the identical `event_id`, but the system isolates them. Exactly 1 case is created for Tenant A, and 1 for Tenant B.

### Claim 4: Deterministic UPI Abuse Detection
**Claim:** The UPI Investigator deterministically reconstructs graph relationships across historical transactions.
**Verification:**
```powershell
python tools/evaluator/test_upi_graph.py
```
**Expected:** Scenarios where a single device uses multiple VPAs within 60 minutes correctly trigger a `upi_abuse_ring` signal and link the device in the evidence graph.

### Claim 5: Absolute Reproducibility
**Claim:** Processing the exact same historical sequence of events will produce the exact same Risk Score and Decision every time.
**Verification:**
```powershell
python tools/evaluator/test_upi_reproducibility.py
```
**Expected:** Evaluates the engine multiple times against the same event payload and verifies that the output hashes (score, signal count, decision) match byte-for-byte.

## 3. The 7 Architectural Invariants

For a deeper dive into the system's design constraints, see the `README.md`.
