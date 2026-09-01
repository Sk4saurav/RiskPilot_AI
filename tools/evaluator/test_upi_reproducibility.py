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

async def setup_db():
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def run_reproducibility():
    await setup_db()
    
    async with async_session() as session:
        org_id = "org_repro"
        org = Organization(id=org_id, name="Repro Org")
        session.add(org)
        
        # Policy
        pol = Policy(
            id="pol_repro", 
            organization_id=org_id, 
            name="Repro Policy", 
            is_active=True, 
            rules_config={"upi_abuse_ring": 25, "HIGH_AMOUNT": 10}, 
            thresholds={"rules": [{"when": {"default": True}, "severity_ranges": {"LOW": [0, 15], "MEDIUM": [16, 24], "HIGH": [25, 100]}}]}, 
            version=1
        )
        session.add(pol)
        await session.commit()
        
        service = InvestigationService()
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Function to create identical scenario
        def create_scenario(suffix):
            events = [
                (f"evt_1_{suffix}", f"dev_R_{suffix}", f"vpa_A", base_time - timedelta(minutes=10)),
                (f"evt_2_{suffix}", f"dev_R_{suffix}", f"vpa_B", base_time - timedelta(minutes=5)),
                (f"evt_3_{suffix}", f"dev_R_{suffix}", f"vpa_C", base_time),
            ]
            for e_id, d_id, vpa, ts in events:
                ev = Event(
                    id=e_id, event_id=e_id, organization_id=org_id, source="api", external_id=e_id,
                    event_type="transaction", payload={"device_id": d_id, "vpa": vpa, "transaction": {"amount_cents": 10000000}}, timestamp=ts
                )
                session.add(ev)
                session.add(EventHistory(id=f"h_{e_id}", event_id=e_id, organization_id=org_id, timestamp=ts, device_id=d_id, vpa=vpa))
                rc = RiskCase(id=f"c_{e_id}", organization_id=org_id, event_id=e_id, status="NEW", created_at=ts)
                session.add(rc)
            return f"c_evt_3_{suffix}", f"dev_R_{suffix}"
            
        case1, dev1 = create_scenario("run1")
        case2, dev2 = create_scenario("run2")
        await session.commit()
        
        # Run 1
        await service.investigate_case(session, case1, "worker_1")
        ra1 = (await session.execute(select(RiskAssessment).where(RiskAssessment.risk_case_id == case1).order_by(RiskAssessment.created_at.desc()))).scalars().first()
        rels1 = (await session.execute(select(Relationship).where(Relationship.source_id == dev1))).scalars().all()
        
        # Run 2
        await service.investigate_case(session, case2, "worker_2")
        ra2 = (await session.execute(select(RiskAssessment).where(RiskAssessment.risk_case_id == case2).order_by(RiskAssessment.created_at.desc()))).scalars().first()
        rels2 = (await session.execute(select(Relationship).where(Relationship.source_id == dev2))).scalars().all()
        
        print("\n--- Reproducibility Test ---")
        match = True
        
        if ra1.risk_score != ra2.risk_score:
            print(f"FAIL Score mismatch: {ra1.risk_score} vs {ra2.risk_score}")
            match = False
        if ra1.recommendation != ra2.recommendation:
            print(f"FAIL Recommendation mismatch: {ra1.recommendation} vs {ra2.recommendation}")
            match = False
        if ra1.signals_snapshot != ra2.signals_snapshot:
            print(f"FAIL Signals mismatch: {ra1.signals_snapshot} vs {ra2.signals_snapshot}")
            match = False
            
        rel_targets_1 = sorted([r.target_id for r in rels1])
        rel_targets_2 = sorted([r.target_id for r in rels2])
        if rel_targets_1 != rel_targets_2:
            print(f"FAIL Relationships mismatch: {rel_targets_1} vs {rel_targets_2}")
            match = False
            
        if match:
            print("PASS SUCCESS: 100% Reproducibility Verified.")
            print(f"Score: {ra1.risk_score}")
            print(f"Signals: {ra1.signals_snapshot}")
            print(f"Relationships: {rel_targets_1}")
        else:
            print("FAIL FAILURE: Results are non-deterministic.")
            
if __name__ == "__main__":
    asyncio.run(run_reproducibility())
