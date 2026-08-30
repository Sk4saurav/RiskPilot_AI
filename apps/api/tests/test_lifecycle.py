import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine
from packages.domain.base import Base
import asyncio
from packages.domain.tenant import Organization, ApiKey
from app.auth import hash_api_key

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
async def setup_org_and_key(client):
    # 1. Create org
    res_org = await client.post("/v1/orgs", json={"name": "Test Org"})
    assert res_org.status_code == 200
    org_id = res_org.json()["id"]

    # 2. Create API key
    res_key = await client.post(f"/v1/orgs/{org_id}/apikeys")
    assert res_key.status_code == 200
    api_key = res_key.json()["key"]

    return org_id, api_key

@pytest.mark.asyncio
async def test_end_to_end_lifecycle_and_idempotency(client, setup_org_and_key):
    org_id, api_key = setup_org_and_key
    headers = {"Authorization": f"Bearer {api_key}"}

    # 1. Ingest Event
    payload = {
        "event_id": "evt_test_123",
        "source": "stripe",
        "external_id": "txn_test_999",
        "event_type": "payment.transaction",
        "occurred_at": "2026-08-23T10:00:00Z",
        "subject": {"type": "customer", "id": "cust_123"},
        "payload": {"amount": 15000, "currency": "USD"}
    }
    
    res1 = await client.post("/v1/events/ingest", json=payload, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["is_new"] == True
    case_id = data1["case"]["id"]
    
    # 2. Ingest Same Event Again (Idempotency)
    res2 = await client.post("/v1/events/ingest", json=payload, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_new"] == False
    assert data2["case"]["id"] == case_id # Resolves to same case
    
    # Verify events count is 1
    # We don't have a direct GET /events, but since is_new=False, it handled idempotency.

    # 3. We will simulate worker running by just verifying the case exists in /cases
    # Since the worker is a separate process we won't run it in this test directly,
    # but we can verify the case is in NEW state.
    res3 = await client.get(f"/v1/cases/{case_id}", headers=headers)
    assert res3.status_code == 200
    assert res3.json()["status"] == "NEW"

    # 4. Try getting timeline
    res4 = await client.get(f"/v1/cases/{case_id}/timeline", headers=headers)
    assert res4.status_code == 200
    assert len(res4.json()) == 0 # No timeline yet because worker hasn't run
