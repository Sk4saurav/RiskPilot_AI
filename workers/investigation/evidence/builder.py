import uuid
from typing import List
from packages.domain import Evidence
from ..schemas import InvestigationFact

class EvidenceBuilder:
    def __init__(self):
        # A simple mapping to turn facts into evidence signals and severity.
        # This acts as the bridge between deterministic facts and policy inputs.
        self.fact_to_signal_map = {
            "DEVICE_SEEN": ("NEW_DEVICE", "MEDIUM", 15),
            "TRANSACTION_AMOUNT": ("HIGH_AMOUNT", "LOW", 10),
            "LOCATION_COUNTRY": ("GEO_IP", "LOW", 5),
            "NETWORK_TYPE": ("VPN_USED", "HIGH", 20),
            "ACCOUNT_AGE": ("NEW_ACCOUNT", "MEDIUM", 10),
            "positive_transaction_history": ("positive_history", "LOW", 0), # Weight will be dynamically applied by PolicyEngine
            "SUPPORT_TICKET_ACTIVE": ("customer_support_verification", "LOW", 0),
            "VIP_ACCOUNT": ("vip_status", "LOW", 0),
        }

    def build_evidence(self, investigation_id: str, facts: List[InvestigationFact]) -> List[Evidence]:
        evidence_list = []
        
        for fact in facts:
            if fact.fact_type in self.fact_to_signal_map:
                signal_type, severity, weight = self.fact_to_signal_map[fact.fact_type]
                
                evidence = Evidence(
                    id=f"ev_{uuid.uuid4().hex[:12]}",
                    investigation_id=investigation_id,
                    evidence_type=signal_type,
                    source=fact.investigator,
                    severity=severity,
                    weight=weight,
                    confidence=fact.confidence,
                    value=fact.value,
                    explanation=f"Derived from {fact.fact_type}"
                )
                evidence_list.append(evidence)
                
        return evidence_list
