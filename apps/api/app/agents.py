from typing import Dict, Any, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.models import Transaction, RiskSignal, InvestigationLog, EntityRelationship

class DetectionEngine:
    """
    Parses incoming events against basic rules.
    Returns True if an investigation is required.
    """
    @staticmethod
    def evaluate(transaction: Transaction) -> bool:
        # Simple heuristics to trigger investigation
        if transaction.amount > 1000:
            return True
        if transaction.location != "New York, USA" and transaction.location != "Chicago, USA": # Assuming baseline
            return True
        if transaction.currency != "USD":
            return True
        return False

class InvestigationAgent:
    """
    Queries the database for related entities.
    Synthesizes a structured Evidence Set (Risk Signals & Graph Edges).
    """
    @classmethod
    async def investigate(cls, db: AsyncSession, transaction: Transaction, risk_event_id: str) -> List[RiskSignal]:
        signals = []
        
        # In a real app, this agent would make LLM calls to construct queries
        # For the hackathon demo, we map the deterministic scenarios
        
        if transaction.amount > 100000:
            signals.append(RiskSignal(
                id=str(uuid.uuid4()), risk_event_id=risk_event_id, 
                signal_type="TRANSACTION_AMOUNT_ANOMALY",
                description=f"Transaction amount {transaction.amount} is 4.2x historical average",
                severity="HIGH", weight=20, source="InvestigationAgent"
            ))
            
        if "dev_unknown" in transaction.device_id:
            signals.append(RiskSignal(
                id=str(uuid.uuid4()), risk_event_id=risk_event_id,
                signal_type="NEW_DEVICE",
                description="Device has never been used by this account",
                severity="MEDIUM", weight=15, source="InvestigationAgent"
            ))
            
        if "203.0.113.42" in transaction.ip_address:
            signals.append(RiskSignal(
                id=str(uuid.uuid4()), risk_event_id=risk_event_id,
                signal_type="SUSPICIOUS_IP_RELATIONSHIP",
                description="IP is associated with 3 previously flagged events",
                severity="CRITICAL", weight=25, source="InvestigationAgent"
            ))
            
            # Create Relationship for Graph
            ip_node = EntityRelationship(
                id=str(uuid.uuid4()), source_entity_type="TRANSACTION", source_entity_id=transaction.id,
                target_entity_type="IP_ADDRESS", target_entity_id="203.0.113.42", relationship_type="USED_IP"
            )
            alert_node = EntityRelationship(
                id=str(uuid.uuid4()), source_entity_type="IP_ADDRESS", source_entity_id="203.0.113.42",
                target_entity_type="ALERT", target_entity_id="PREV_ALERT_921", relationship_type="FLAGGED_IN"
            )
            db.add_all([ip_node, alert_node])
            
        if transaction.location not in ["New York, USA", "Chicago, USA"]:
            signals.append(RiskSignal(
                id=str(uuid.uuid4()), risk_event_id=risk_event_id,
                signal_type="GEOGRAPHIC_ANOMALY",
                description=f"Transaction occurred from a new geographic location: {transaction.location}",
                severity="HIGH", weight=18, source="InvestigationAgent"
            ))
            
            loc_node = EntityRelationship(
                id=str(uuid.uuid4()), source_entity_type="TRANSACTION", source_entity_id=transaction.id,
                target_entity_type="LOCATION", target_entity_id=transaction.location, relationship_type="OCCURRED_IN"
            )
            db.add(loc_node)
            
        if transaction.amount > 200000:
            signals.append(RiskSignal(
                id=str(uuid.uuid4()), risk_event_id=risk_event_id,
                signal_type="VELOCITY_ANOMALY",
                description="Transaction velocity exceeds 99th percentile for account",
                severity="MEDIUM", weight=10, source="InvestigationAgent"
            ))
            signals.append(RiskSignal(
                id=str(uuid.uuid4()), risk_event_id=risk_event_id,
                signal_type="HISTORICAL_DEVIATION",
                description="Activity deviates from historical baseline behavior",
                severity="LOW", weight=6, source="InvestigationAgent"
            ))
            
        db.add_all(signals)
        await db.commit()
        return signals

class DecisionAgent:
    """
    Analyzes the Risk Score to recommend an action and provides rationale.
    """
    @classmethod
    def recommend(cls, score: int, signals: List[RiskSignal]) -> Dict[str, str]:
        recommendation = "APPROVE"
        rationale = "Transaction conforms to expected baseline behavior."
        
        if score >= 80:
            recommendation = "HOLD + ESCALATE"
            rationale = "Multiple independent risk indicators correlate with previously flagged activity."
        elif score >= 60:
            recommendation = "ESCALATE"
            rationale = "High risk score based on anomalous behavioral indicators requiring manual review."
        elif score >= 30:
            recommendation = "VERIFY"
            rationale = "Medium risk score due to slight deviations from baseline behavior."
            
        evidence_completeness = min(100, 60 + (len(signals) * 8)) # Simulated metric
            
        return {
            "recommendation": recommendation,
            "rationale": rationale,
            "evidence_completeness": f"{evidence_completeness}%"
        }
