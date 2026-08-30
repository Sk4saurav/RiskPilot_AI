import uuid
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.domain import Policy
from packages.domain.validation import ReplayDataset, ReplayRun, ReplayEvent, ValidationResult
from workers.investigation.service import InvestigationService

class ReplayEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.investigation_service = InvestigationService()
        
    async def run_dataset(self, dataset_id: str) -> str:
        """
        Executes a blind replay of the historical dataset without polluting production cases.
        Returns the ReplayRun ID.
        """
        # 1. Fetch Dataset
        ds_res = await self.session.execute(select(ReplayDataset).where(ReplayDataset.id == dataset_id))
        dataset = ds_res.scalar_one_or_none()
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
            
        org_id = dataset.organization_id
        
        # 2. Fetch Active Policy
        pol_res = await self.session.execute(
            select(Policy).where(Policy.organization_id == org_id, Policy.is_active == True).limit(1)
        )
        policy = pol_res.scalar_one_or_none()
        
        # 3. Create Run Record
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        run = ReplayRun(
            id=run_id,
            dataset_id=dataset_id,
            status="RUNNING",
            policy_version=policy.version if policy else None,
            configuration_snapshot={
                "policy_id": policy.id if policy else None,
                "investigators": [inv.__class__.__name__ for inv in self.investigation_service.investigators]
            }
        )
        self.session.add(run)
        await self.session.commit()
        
        # 4. Fetch Events
        ev_res = await self.session.execute(select(ReplayEvent).where(ReplayEvent.dataset_id == dataset_id))
        events = ev_res.scalars().all()
        
        # 5. Execute Replay
        for event in events:
            # We time the in-memory RiskPilot investigation to compute absolute metrics
            start_time = time.time()
            
            # Step 5a: Gather Facts blindly
            all_facts = []
            for investigator in self.investigation_service.investigators:
                res = await investigator.investigate(event.normalized_event, event.historical_context_snapshot or {})
                all_facts.extend(res.facts)
                
            # Step 5b: Execute Pure Logic
            # We mock the case_id and investigation_id since they don't persist
            mock_case_id = f"mock_case_{uuid.uuid4().hex[:8]}"
            mock_inv_id = f"mock_inv_{uuid.uuid4().hex[:8]}"
            
            evidence_list, relationships, assessment = self.investigation_service.execute_investigation_logic(
                mock_case_id, all_facts, policy, mock_inv_id
            )
            
            end_time = time.time()
            riskpilot_inv_time = int(end_time - start_time)
            
            # Step 5c: Compute Simulated Analyst Review Time
            # For Alpha 0.6 v0.1, we assume a conservative 3 minutes (180 seconds) if RiskPilot recommends ESCALATE or HOLD
            # and 60 seconds if APPROVE, or we could just use a flat 180s.
            recommendation = assessment.recommendation if assessment else "APPROVE"
            riskpilot_analyst_time = 180 if recommendation in ["ESCALATE", "HOLD"] else 60
            
            # Step 5d: Compute Metrics
            manual_total = (event.manual_investigation_time_sec or 0) + (event.manual_analyst_time_sec or 0)
            rp_total = riskpilot_inv_time + riskpilot_analyst_time
            time_saved_sec = manual_total - rp_total
            time_saved_percent = (time_saved_sec / manual_total * 100) if manual_total > 0 else 0
            
            # Simple Evidence Coverage (Placeholder logic for v0.1: match keys)
            # A real implementation would parse the textual manual evidence against the evidence_list types
            evidence_coverage_percent = 100.0 if evidence_list else 0.0
            
            decision_match = False
            if event.manual_decision:
                md = event.manual_decision.strip().upper()
                hd = recommendation.strip().upper()
                if md == hd or (md == "APPROVE" and hd == "APPROVE") or (md == "HOLD" and hd in ["HOLD", "ESCALATE"]):
                    decision_match = True
            
            # Step 5e: Persist Validation Result
            result = ValidationResult(
                id=f"res_{uuid.uuid4().hex[:12]}",
                run_id=run_id,
                event_id=event.id,
                riskpilot_investigation_time_sec=riskpilot_inv_time,
                riskpilot_analyst_time_sec=riskpilot_analyst_time,
                riskpilot_recommendation=recommendation,
                riskpilot_decision=recommendation, # Simulated auto-acceptance of recommendation
                riskpilot_score=assessment.risk_score if assessment else 0,
                evidence_snapshot=[{"type": ev.evidence_type, "severity": ev.severity, "weight": ev.weight, "source": ev.source, "value": ev.value} for ev in evidence_list],
                signals_snapshot=assessment.signals_snapshot if assessment else [],
                evidence_coverage_percent=evidence_coverage_percent,
                time_saved_sec=time_saved_sec,
                time_saved_percent=time_saved_percent,
                decision_match=decision_match
            )
            self.session.add(result)
            
        run.status = "COMPLETED"
        run.completed_at = datetime.utcnow()
        await self.session.commit()
        
        return run_id
