import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import engine
from packages.domain.base import Base
import asyncio

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
    res_org = await client.post("/v1/orgs", json={"name": "Test Org 2"})
    org_id = res_org.json()["id"]
    res_key = await client.post(f"/v1/orgs/{org_id}/apikeys")
    api_key = res_key.json()["key"]
    return org_id, api_key

@pytest.mark.asyncio
async def test_policy_reproducibility(client, setup_org_and_key):
    org_id, api_key = setup_org_and_key
    headers = {"Authorization": f"Bearer {api_key}"}

    # 1. Create Policy v1
    policy_payload = {
        "organization_id": org_id,
        "name": "Global Fraud Policy",
        "rules_config": {"GEO_IP": 25},
        "thresholds": {"CRITICAL": 80, "HIGH": 60, "MEDIUM": 40},
        "is_active": True
    }
    res_p1 = await client.post("/v1/policies", json=policy_payload, headers=headers)
    assert res_p1.status_code == 200
    p1 = res_p1.json()
    assert p1["version"] == 1

    # 2. Update to Policy v2
    policy_payload["rules_config"] = {"GEO_IP": 35}
    res_p2 = await client.put(f"/v1/policies/{p1['id']}", json=policy_payload, headers=headers)
    assert res_p2.status_code == 200
    p2 = res_p2.json()
    assert p2["version"] == 2
    
    # Prove they both exist, and v1 is inactive, v2 is active
    res_list = await client.get("/v1/policies?active_only=false", headers=headers)
    policies = res_list.json()
    assert len(policies) == 2
    
    active_policies = await client.get("/v1/policies?active_only=true", headers=headers)
    assert len(active_policies.json()) == 1
    assert active_policies.json()[0]["version"] == 2
