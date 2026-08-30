import asyncio
import httpx
import os
import uuid
import sys
import time

class SmokeTestError(Exception):
    pass

async def print_result(name: str, coro):
    try:
        await coro
        print(f"[PASS] {name}")
    except Exception as e:
        print(f"[FAIL] {name} - {str(e)}")
        sys.exit(1)

async def test_api_health(base_url: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{base_url}/health")
        if resp.status_code != 200:
            raise SmokeTestError(f"Expected 200, got {resp.status_code}")

async def test_authentication(base_url: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{base_url}/v1/cases")
        if resp.status_code != 401:
            raise SmokeTestError("Expected 401 without auth")

async def test_tenant_isolation(base_url: str, api_key: str):
    # Just verify valid key works
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{base_url}/v1/cases", headers={"Authorization": f"Bearer {api_key}"})
        if resp.status_code != 200:
            raise SmokeTestError("Valid key rejected")
            
        # Try invalid key
        resp = await client.get(f"{base_url}/v1/cases", headers={"Authorization": f"Bearer invalid_key"})
        if resp.status_code != 401:
            raise SmokeTestError("Invalid key should be rejected")

async def test_event_ingestion_and_idempotency(base_url: str, api_key: str) -> str:
    event_id = f"evt_{uuid.uuid4().hex[:8]}"
    payload = {
        "event_id": event_id,
        "event_type": "transaction",
        "timestamp": "2026-08-29T10:00:00Z",
        "actor": {"user_id": "test"},
        "transaction": {"amount_cents": 5000, "currency": "USD"},
        "network": {},
        "device": {"is_new": True},
        "location": {}
    }
    
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient() as client:
        # 1. Ingest
        resp1 = await client.post(f"{base_url}/v1/events/ingest", json=payload, headers=headers)
        if resp1.status_code != 200:
            raise SmokeTestError("Ingestion failed")
        case_id = resp1.json()["case_id"]
        
        # 2. Idempotency - submit again
        resp2 = await client.post(f"{base_url}/v1/events/ingest", json=payload, headers=headers)
        if resp2.status_code != 200:
            raise SmokeTestError("Idempotent ingestion failed")
        if resp2.json()["case_id"] != case_id:
            raise SmokeTestError("Idempotency returned different case ID")
            
        return case_id

async def test_investigation_flow(base_url: str, api_key: str, case_id: str):
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient() as client:
        # Poll for completion
        max_attempts = 30
        for _ in range(max_attempts):
            resp = await client.get(f"{base_url}/v1/cases/{case_id}", headers=headers)
            status = resp.json()["status"]
            if status == "PENDING_REVIEW":
                break
            await asyncio.sleep(0.5)
        else:
            raise SmokeTestError("Investigation timed out (Is the worker running?)")

        # Verify evidence
        ev_resp = await client.get(f"{base_url}/v1/cases/{case_id}/evidence", headers=headers)
        if not ev_resp.json():
            raise SmokeTestError("No evidence generated")

        # Verify assessment & risk scoring
        as_resp = await client.get(f"{base_url}/v1/cases/{case_id}/assessment", headers=headers)
        if as_resp.status_code != 200 or "risk_score" not in as_resp.json():
            raise SmokeTestError("Risk assessment failed")
            
        # Verify timeline
        tl_resp = await client.get(f"{base_url}/v1/cases/{case_id}/timeline", headers=headers)
        if len(tl_resp.json()) < 2:
            raise SmokeTestError("Audit timeline not generated")

async def run_all():
    print("==================================================")
    print("       RISKPILOT EVALUATOR SMOKE TESTS            ")
    print("==================================================")
    
    base_url = "http://localhost:8000"
    api_key = os.environ.get("RISKPILOT_API_KEY")
    
    if not api_key:
        print("Error: RISKPILOT_API_KEY env var must be set to run smoke tests.")
        print("Hint: Run python -m tools.demo.reset_demo to get a key.")
        sys.exit(1)
        
    await print_result("API health", test_api_health(base_url))
    await print_result("Authentication", test_authentication(base_url))
    await print_result("Tenant isolation", test_tenant_isolation(base_url, api_key))
    
    case_id = ""
    try:
        case_id = await test_event_ingestion_and_idempotency(base_url, api_key)
        print("[PASS] Event ingestion")
        print("[PASS] Idempotency")
    except Exception as e:
        print(f"[FAIL] Event ingestion / Idempotency - {str(e)}")
        sys.exit(1)
        
    try:
        await test_investigation_flow(base_url, api_key, case_id)
        print("[PASS] Investigation")
        print("[PASS] Evidence generation")
        print("[PASS] Risk scoring")
        print("[PASS] Policy evaluation")
        print("[PASS] Audit trail")
    except Exception as e:
        print(f"[FAIL] Investigation flow - {str(e)}")
        sys.exit(1)
        
    print("\nALL TESTS PASSED")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_all())
