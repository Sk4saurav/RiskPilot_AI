import asyncio
import uuid
import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import select
from apps.api.app.database import async_session, engine as db_engine
from packages.domain.base import Base
from packages.domain import Organization, Policy, Event, EventHistory, RiskCase, RiskAssessment, Relationship, Evidence
from workers.investigation.service import InvestigationService
from tools.provision_design_partner import provision

async def setup_db():
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Run the design partner provision to get org and policy
    await provision()

async def create_event(session, org_id, device_id, vpa, timestamp, amount_cents=1000):
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    payload = {
        "event_id": event_id,
        "device_id": device_id,
        "vpa": vpa,
        "transaction": {"amount_cents": amount_cents}
    }
    event = Event(
        id=event_id,
        event_id=event_id,
        organization_id=org_id,
        source="api",
        external_id=event_id,
        event_type="transaction",
        payload=payload,
        timestamp=timestamp
    )
    session.add(event)
    
    # Create History
    history_record = EventHistory(
        id=f"evh_{uuid.uuid4().hex[:12]}",
        event_id=event.id,
        organization_id=org_id,
        timestamp=event.timestamp,
        device_id=device_id,
        vpa=vpa,
        customer_id="cust_test"
    )
    session.add(history_record)
    
    case_id = f"case_{uuid.uuid4().hex[:12]}"
    risk_case = RiskCase(
        id=case_id,
        organization_id=org_id,
        event_id=event.id,
        status="NEW",
        created_at=datetime.utcnow()
    )
    session.add(risk_case)
    await session.commit()
    return case_id

async def run_scenarios():
    await setup_db()
    
    async with async_session() as session:
        # Get the provisioned org
        result = await session.execute(select(Organization).limit(1))
        org = result.scalar_one()
        org_id = org.id
        
        # Create second org for tenant isolation test
        org_id_b = "org_b_test"
        org_b = Organization(id=org_id_b, name="Tenant B")
        session.add(org_b)
        
        # Give Org B the same policy
        pol_b = Policy(id="pol_b_test", organization_id=org_id_b, name="Tenant B Policy", is_active=True, rules_config={"upi_abuse_ring": 25}, thresholds={"rules": [{"when": {"default": True}, "severity_ranges": {"LOW": [0, 100]}}]}, version=1)
        session.add(pol_b)
        await session.commit()
        
        service = InvestigationService()
        now = datetime.utcnow()
        
        scenarios = []
        
        # Scenario 1: 1 VPA / device (No abuse)
        s1_case = await create_event(session, org_id, "dev_1", "alice@upi", now)
        scenarios.append(("Scenario 1 (1 VPA)", s1_case, False))
        
        # Scenario 2: 2 VPAs / device (No abuse)
        await create_event(session, org_id, "dev_2", "alice@upi", now - timedelta(minutes=5))
        s2_case = await create_event(session, org_id, "dev_2", "bob@upi", now)
        scenarios.append(("Scenario 2 (2 VPAs)", s2_case, False))
        
        # Scenario 3: 3 VPAs / device (Threshold behavior)
        await create_event(session, org_id, "dev_3", "alice@upi", now - timedelta(minutes=10))
        await create_event(session, org_id, "dev_3", "bob@upi", now - timedelta(minutes=5))
        s3_case = await create_event(session, org_id, "dev_3", "charlie@upi", now)
        scenarios.append(("Scenario 3 (3 VPAs)", s3_case, True))
        
        # Scenario 4: 4 VPAs / device (Abuse evidence - scores 25+)
        await create_event(session, org_id, "dev_4", "alice@upi", now - timedelta(minutes=15))
        await create_event(session, org_id, "dev_4", "bob@upi", now - timedelta(minutes=10))
        await create_event(session, org_id, "dev_4", "charlie@upi", now - timedelta(minutes=5))
        s4_case = await create_event(session, org_id, "dev_4", "david@upi", now)
        scenarios.append(("Scenario 4 (4 VPAs)", s4_case, True))
        
        # Scenario 5: Same VPA repeatedly (No ring)
        await create_event(session, org_id, "dev_5", "alice@upi", now - timedelta(minutes=10))
        await create_event(session, org_id, "dev_5", "alice@upi", now - timedelta(minutes=5))
        s5_case = await create_event(session, org_id, "dev_5", "alice@upi", now)
        scenarios.append(("Scenario 5 (Same VPA)", s5_case, False))
        
        # Scenario 6: Different devices, same VPA (No device ring)
        await create_event(session, org_id, "dev_6a", "alice@upi", now - timedelta(minutes=10))
        await create_event(session, org_id, "dev_6b", "bob@upi", now - timedelta(minutes=5))
        s6_case = await create_event(session, org_id, "dev_6c", "charlie@upi", now)
        scenarios.append(("Scenario 6 (Diff Devices)", s6_case, False))
        
        # Scenario 7: Transactions outside 60min window (Not counted)
        await create_event(session, org_id, "dev_7", "alice@upi", now - timedelta(minutes=65))
        await create_event(session, org_id, "dev_7", "bob@upi", now - timedelta(minutes=61))
        s7_case = await create_event(session, org_id, "dev_7", "charlie@upi", now)
        scenarios.append(("Scenario 7 (>60m window)", s7_case, False))
        
        # Scenario 8: Tenant isolation (Transactions from Org B do not cross-pollinate to Org A)
        await create_event(session, org_id_b, "dev_8", "alice@upi", now - timedelta(minutes=10))
        await create_event(session, org_id_b, "dev_8", "bob@upi", now - timedelta(minutes=5))
        s8_case = await create_event(session, org_id, "dev_8", "charlie@upi", now)
        scenarios.append(("Scenario 8 (Tenant Isolation)", s8_case, False))
        
        print("\n--- Running Evaluator Scenarios ---")
        passed = 0
        for name, case_id, expects_abuse in scenarios:
            await service.investigate_case(session, case_id, "evaluator")
            
            # Check results
            assessment = (await session.execute(select(RiskAssessment).where(RiskAssessment.risk_case_id == case_id))).scalar_one_or_none()
            has_abuse = "upi_abuse_ring" in (assessment.signals_snapshot if assessment else [])
            score = assessment.risk_score if assessment else 0
            
            if has_abuse == expects_abuse:
                print(f"PASS {name}: (Has Abuse: {has_abuse}, Score: {score})")
                passed += 1
            else:
                print(f"FAIL {name}: Expected abuse={expects_abuse} but got {has_abuse}")
                
            # If expects abuse, assert relationships exist
            if expects_abuse:
                # Find device_id
                evt = (await session.execute(select(Event).join(RiskCase).where(RiskCase.id == case_id))).scalar_one()
                dev_id = evt.payload["device_id"]
                rels = (await session.execute(select(Relationship).where(Relationship.source_id == dev_id, Relationship.relationship_type == "associated_vpa"))).scalars().all()
                if len(rels) < 3:
                    print(f"FAIL {name}: Expected >=3 'associated_vpa' relationships for {dev_id}, found {len(rels)}")
                    passed -= 1
                    
        print(f"\nTotal: {passed}/{len(scenarios)} passed.")
        
if __name__ == "__main__":
    asyncio.run(run_scenarios())
