import asyncio
import uuid
import sys
import os

from apps.api.app.database import async_session
from packages.domain import RiskCase, Event

async def trigger_case():
    org_id = "org_dp_54a219a9"
    test_event_id = f"tx_live_{uuid.uuid4().hex[:6]}"
    
    print(f"[*] Triggering live case for event: {test_event_id}")
    
    # We can just hit the API endpoint using httpx or TestClient, or directly ingest.
    # The easiest is using httpx against localhost:8000
    import httpx
    import json
    
    payload = {
        "customer_event_id": test_event_id,
        "timestamp": "2026-08-27T10:00:00Z",
        "customer_id": "cust_live_1",
        "tx_amount": 250000,
        "currency": "INR",
        "ip": "100.100.100.100",
        "country_code": "RU",
        "city": "Moscow",
        "device_is_new": True
    }
    
    async with httpx.AsyncClient() as client:
        # We need the API key for ingest
        response = await client.post(
            "http://localhost:8000/v1/integrations/design_partner/events",
            json=payload,
            headers={
                "Authorization": "Bearer rp_live_-scQQFQZti_PMqZQF_WhP1RmFHl5z7QvTLl0H31GuHI"
            }
        )
        print("API Response:", response.status_code, response.text)
        
    print("[*] Waiting a moment for background worker to process investigation...")
    await asyncio.sleep(2)
    
    async with async_session() as session:
        # Check case status
        from sqlalchemy import select
        res = await session.execute(select(RiskCase).where(RiskCase.event_id == test_event_id))
        case = res.scalar_one_or_none()
        if case:
            print(f"[*] Case {case.id} is now in status: {case.status}")
        else:
            print("[!] Case not found yet.")

if __name__ == "__main__":
    asyncio.run(trigger_case())
