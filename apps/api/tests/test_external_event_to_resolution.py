import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.main import app
from app.database import get_db, engine
from packages.domain.base import Base
from workers.investigation.runner import InvestigationRunner
from packages.domain import RiskCase, Evidence, RiskAssessment, AuditTrail
from sqlalchemy.orm import sessionmaker

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_external_event_to_resolution():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Organization
        org_res = await client.post("/v1/orgs", json={"name": "Acme Corp"})
        assert org_res.status_code == 200
        org_id = org_res.json()["id"]

        # 2. Create API Key
        key_res = await client.post(f"/v1/orgs/{org_id}/apikeys")
        assert key_res.status_code == 200
        api_key = key_res.json()["key"]
        
        headers = {"Authorization": f"Bearer {api_key}"}
        user_headers = {"X-Alpha-Organization-Id": org_id}

        # 3. Create Policy (acting as user)
        policy_res = await client.post(
            "/v1/policies",
            json={
                "name": "Acme Default",
                "rules_config": {"HIGH_AMOUNT": 20, "VPN_USED": 25},
                "thresholds": {
                    "LOW": [0, 29],
                    "MEDIUM": [30, 59],
                    "HIGH": [60, 79],
                    "CRITICAL": [80, 100]
                }
            },
            headers=user_headers
        )
        if policy_res.status_code != 200:
            print(f"Policy Creation Failed: {policy_res.text}")
        assert policy_res.status_code == 200
        
        # 4. Send External Event
        event_payload = {
            "event_id": "evt_001",
            "source": "payment_gateway",
            "external_id": "tx_1001",
            "event_type": "transaction",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "subject": {"type": "user", "id": "user_404"},
            "payload": {"amount": 5000, "ip": "192.168.1.1"}
        }
        ingest_res = await client.post("/v1/events/ingest", json=event_payload, headers=headers)
        assert ingest_res.status_code == 200
        case_id = ingest_res.json()["case"]["id"]
        
        async with async_session_maker() as db_session:
            cases = (await db_session.execute(select(RiskCase))).scalars().all()

        # 5. Worker Investigates
        runner = InvestigationRunner(async_session_maker, "worker_test")
        await runner._run_loop_cycle()

        # 6. Verify Case Status & Evidence
        case_check = await client.get(f"/v1/cases/{case_id}", headers=user_headers)
        assert case_check.status_code == 200
        case_data = case_check.json()
        assert case_data["status"] == "PENDING_REVIEW"
        
        assessment_check = await client.get(f"/v1/cases/{case_id}/assessment", headers=user_headers)
        assert assessment_check.status_code == 200
        assessment_data = assessment_check.json()
        try:
            assert assessment_data["risk_score"] > 0
        except AssertionError as e:
            with open("DEBUG_OUT.txt", "w") as f:
                f.write(f"RISK_SCORE_FAILED: {assessment_data}\n")
            raise e
        
        # 7. Ask Copilot
        copilot_res = await client.post(
            f"/v1/cases/{case_id}/copilot/ask",
            json={"query": "Why was this flagged?"},
            headers=user_headers
        )
        assert copilot_res.status_code == 200
        copilot_data = copilot_res.json()
        assert "answer" in copilot_data
        assert "evidence_references" in copilot_data

        # 8. Human Decision
        decision_res = await client.post(
            f"/v1/cases/{case_id}/decisions",
            json={"human_decision": "ESCALATE", "reason": "High amount and bad IP", "actor_id": "test_analyst"},
            headers=user_headers
        )
        assert decision_res.status_code == 200

        # 9. Verify Audit Trail
        async for db in get_db():
            audits = (await db.execute(select(AuditTrail).where(AuditTrail.entity_id == case_id))).scalars().all()
            actions = [a.action for a in audits]
            assert "CASE_CREATED" in actions
            assert "HUMAN_DECISION" in actions
            break

        # --------------------------------
        # Test Idempotency
        # --------------------------------
        ingest_res_2 = await client.post("/v1/events/ingest", json=event_payload, headers=headers)
        assert ingest_res_2.status_code == 200
        assert ingest_res_2.json()["case"]["id"] == case_id

        # --------------------------------
        # Test Multi-tenancy
        # --------------------------------
        org2_res = await client.post("/v1/orgs", json={"name": "Beta Corp"})
        org2_id = org2_res.json()["id"]
        
        user2_headers = {"X-Alpha-Organization-Id": org2_id}
        case_check_forbidden = await client.get(f"/v1/cases/{case_id}", headers=user2_headers)
        assert case_check_forbidden.status_code == 404

        # --------------------------------
        # Test Policy Immutability
        # --------------------------------
        # Case A is already evaluated with v1. Let's update policy.
        policy_id = policy_res.json()["id"]
        policy_update = await client.put(
            f"/v1/policies/{policy_id}",
            json={
                "name": "Acme Default",
                "rules_config": {"HIGH_AMOUNT": 35, "VPN_USED": 35},
                "thresholds": {
                    "LOW": [0, 29],
                    "MEDIUM": [30, 59],
                    "HIGH": [60, 79],
                    "CRITICAL": [80, 100]
                }
            },
            headers=user_headers
        )
        assert policy_update.status_code == 200
        
        # Check Case A again, score should be the same (still using v1)
        assessment_check_again = await client.get(f"/v1/cases/{case_id}/assessment", headers=user_headers)
        assert assessment_check_again.json()["risk_score"] == assessment_data["risk_score"]
