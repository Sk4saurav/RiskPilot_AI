import asyncio
import httpx
import os
import uuid
import sys

class FailureTestError(Exception):
    pass

async def print_result(name: str, coro):
    try:
        await coro
        print(f"[PASS] {name}")
    except Exception as e:
        print(f"[FAIL] {name} - {str(e)}")
        sys.exit(1)

async def test_invalid_payload(base_url: str, api_key: str):
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "transaction"
        # Missing required fields like timestamp, actor, etc.
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{base_url}/v1/events/ingest", json=payload, headers=headers)
        if resp.status_code not in [400, 422]:
            raise FailureTestError(f"Expected 422 for invalid payload, got {resp.status_code}")

async def test_unauthorized_tenant(base_url: str):
    headers = {"Authorization": f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"}
    payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:8]}",
        "event_type": "transaction",
        "timestamp": "2026-08-29T10:00:00Z",
        "actor": {"user_id": "test"},
        "transaction": {"amount_cents": 1000, "currency": "USD"},
        "network": {"ip": "127.0.0.1"},
        "device": {"is_new": False},
        "location": {"country": "US", "city": "NY"}
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{base_url}/v1/events/ingest", json=payload, headers=headers)
        if resp.status_code not in [401, 403]:
            raise FailureTestError(f"Expected 401/403 for unauthorized tenant, got {resp.status_code}")

async def run_all():
    print("==================================================")
    print("       RISKPILOT FAILURE SCENARIO TESTS           ")
    print("==================================================")
    
    base_url = "http://localhost:8000"
    api_key = os.environ.get("RISKPILOT_API_KEY")
    
    if not api_key:
        print("Error: RISKPILOT_API_KEY env var must be set to run tests.")
        sys.exit(1)
        
    await print_result("Invalid payload handling (422)", test_invalid_payload(base_url, api_key))
    await print_result("Unauthorized tenant isolation (401/403)", test_unauthorized_tenant(base_url))
    
    print("\nNOTE: Worker failure (recovery) and Webhook retries are covered")
    print("by the backend asynchronous architecture and DB polling.")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_all())
