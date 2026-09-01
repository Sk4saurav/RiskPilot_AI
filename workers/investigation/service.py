import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.domain import RiskCase, Investigation, RiskAssessment, Policy, AuditTrail
from packages.risk_engine.evaluation.engine import PolicyEngine

from .investigators.device import DeviceInvestigator
from .investigators.transaction import TransactionInvestigator
from .investigators.location import LocationInvestigator
from .investigators.network import NetworkInvestigator
from .investigators.history import HistoryInvestigator
from .investigators.context import CustomerContextInvestigator
from .evidence.builder import EvidenceBuilder
from .correlation.relationships import RelationshipBuilder

from packages.utils.logger import setup_logger, log_event
from .investigators.repositories import SQLAlchemyUPIHistoryRepository

logger = setup_logger("worker.investigation")

class InvestigationService:
    def __init__(self):
        # We will lazily instantiate investigators that need a DB session inside investigate_case
        self.evidence_builder = EvidenceBuilder()
        self.relationship_builder = RelationshipBuilder()
        
    async def investigate_case(self, session: AsyncSession, case_id: str, worker_id: str) -> bool:
        """
        Orchestrates the investigation of a case.
        """
        # 1. Fetch case and event
        result = await session.execute(
            select(RiskCase).where(RiskCase.id == case_id)
        )
        case = result.scalar_one_or_none()
        if not case:
            return False
            
        # Get Event Payload
        await session.refresh(case, ["event"])
        event_payload = case.event.payload or {}
        org_id = case.event.organization_id
        
        # Inject controlled failure for Chaos Lab
        device_id = event_payload.get("device_id") or event_payload.get("device", {}).get("id") or ""
        if isinstance(device_id, str) and "CHAOS_DELAY_" in device_id:
            import asyncio
            try:
                delay_sec = int(device_id.split("CHAOS_DELAY_")[1])
                await asyncio.sleep(delay_sec)
            except ValueError:
                pass
        
        # 2. Create Investigation record
        investigation = Investigation(
            id=f"inv_{uuid.uuid4().hex[:12]}",
            risk_case_id=case_id,
            status="IN_PROGRESS"
        )
        session.add(investigation)
        
        # Audit: Investigation Started
        self._add_audit(session, case_id, "INVESTIGATION_STARTED", worker_id, {"investigation_id": investigation.id})
        log_event(logger, "investigation_started", case_id=case_id, worker_id=worker_id, investigation_id=investigation.id)
        
        # 3. Collect Facts
        all_facts = []
        
        from .investigators.upi import UPIInvestigator
        upi_repo = SQLAlchemyUPIHistoryRepository(session)
        
        investigators = [
            TransactionInvestigator(),
            DeviceInvestigator(),
            LocationInvestigator(),
            NetworkInvestigator(),
            HistoryInvestigator(),
            CustomerContextInvestigator(),
            UPIInvestigator(repository=upi_repo, config={"distinct_vpa_threshold": 3})
        ]
        
        context = {
            "org_id": org_id,
            "event_timestamp": case.event.timestamp
        }
        
        for investigator in investigators:
            res = await investigator.investigate(event_payload, context)
            all_facts.extend(res.facts)
            
        # Audit: Facts Collected
        self._add_audit(session, case_id, "FACTS_COLLECTED", worker_id, {"fact_count": len(all_facts)})
        log_event(logger, "facts_collected", case_id=case_id, fact_count=len(all_facts))
            
        # 4. Build Evidence & Evaluate Policy using pure logic
        pol_res = await session.execute(
            select(Policy).where(Policy.organization_id == org_id, Policy.is_active == True).limit(1)
        )
        policy = pol_res.scalar_one_or_none()
        
        evidence_list, relationships, assessment = self.execute_investigation_logic(case_id, all_facts, policy, investigation.id)
        
        # Persist generated entities
        for ev in evidence_list:
            session.add(ev)
        for rel in relationships:
            session.add(rel)
        if assessment:
            session.add(assessment)
            
        # Audits for generated entities
        self._add_audit(session, case_id, "EVIDENCE_CREATED", worker_id, {"evidence_count": len(evidence_list)})
        self._add_audit(session, case_id, "RELATIONSHIPS_DISCOVERED", worker_id, {"relationship_count": len(relationships)})
        if assessment:
            self._add_audit(session, case_id, "RISK_ASSESSED", worker_id, {"score": assessment.risk_score})
            log_event(logger, "risk_assessed", case_id=case_id, score=assessment.risk_score, policy_version=policy.version if policy else None)
            
        # 7. Complete Investigation
        investigation.status = "COMPLETED"
        investigation.completed_at = datetime.utcnow()
        case.completed_at = datetime.utcnow()
        
        # 8. Transition Case
        case.transition_to("PENDING_REVIEW", session, user_id=worker_id)
        
        # Audit: Investigation Completed
        self._add_audit(session, case_id, "INVESTIGATION_COMPLETED", worker_id, {})
        log_event(logger, "investigation_completed", case_id=case_id, new_status="PENDING_REVIEW")
        
        # 9. Dispatch Webhook
        from packages.utils.webhooks import dispatch_webhook
        await dispatch_webhook(
            session=session, 
            org_id=org_id, 
            event_type="case.risk_assessed",
            payload={"case_id": case.id, "status": "PENDING_REVIEW", "risk_score": assessment.risk_score if assessment else None}
        )
        
        await session.commit()
        return True
        
    def execute_investigation_logic(self, case_id: str, all_facts: list, policy: Optional[Policy], investigation_id: str):
        """
        Pure logic separated from SQLAlchemy persistence, callable by the ReplayEngine.
        """
        # Build Evidence
        evidence_list = self.evidence_builder.build_evidence(investigation_id, all_facts)
        
        # Build Correlation
        relationships = self.relationship_builder.build_relationships(case_id, all_facts)
        
        # Evaluate Policy
        assessment = None
        if policy:
            score = PolicyEngine.evaluate(policy, evidence_list)
            
            # Extract PolicyContext from facts
            context = {}
            for fact in all_facts:
                if fact.fact_type == "TRANSACTION_AMOUNT" and isinstance(fact.value, dict):
                    context["amount_cents"] = fact.value.get("amount")
                    
            severity, rule_rationale = PolicyEngine.determine_severity(policy, score, context=context)
            
            assessment = RiskAssessment(
                id=f"ra_{uuid.uuid4().hex[:12]}",
                risk_case_id=case_id,
                policy_id=policy.id,
                policy_version=policy.version,
                policy_snapshot=policy.rules_config,
                signals_snapshot=[ev.evidence_type for ev in evidence_list],
                risk_score=score,
                recommendation="ESCALATE" if severity in ["HIGH", "CRITICAL"] else "APPROVE",
                rationale=f"Score: {score}. Severity: {severity}. {rule_rationale}"
            )
            
        return evidence_list, relationships, assessment

    def _add_audit(self, session, case_id, action, worker_id, metadata):
        audit = AuditTrail(
            id=f"audit_{uuid.uuid4().hex[:12]}",
            entity_type="RiskCase",
            entity_id=case_id,
            action=action,
            user_id=worker_id,
            metadata_json=metadata
        )
        session.add(audit)
