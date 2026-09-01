import uuid
from typing import List
from ..schemas import InvestigationFact
from packages.domain import Relationship

class RelationshipBuilder:
    def build_relationships(self, case_id: str, facts: List[InvestigationFact]) -> List[Relationship]:
        """
        Extracts relationships from facts to build entity correlations.
        """
        relationships = []
        
        for fact in facts:
            if "ip" in fact.value:
                relationships.append(Relationship(
                    id=f"rel_{uuid.uuid4().hex[:12]}",
                    source_id=case_id,
                    target_id=fact.value["ip"],
                    relationship_type="via"
                ))
            if "device_id" in fact.value:
                relationships.append(Relationship(
                    id=f"rel_{uuid.uuid4().hex[:12]}",
                    source_id=case_id,
                    target_id=fact.value["device_id"],
                    relationship_type="used"
                ))
            if fact.fact_type in ["upi_velocity", "upi_abuse_ring"]:
                device_id = fact.value.get("device_id")
                vpa_list = fact.value.get("vpa_list", [])
                for vpa in vpa_list:
                    relationships.append(Relationship(
                        id=f"rel_{uuid.uuid4().hex[:12]}",
                        source_id=device_id,
                        target_id=vpa,
                        relationship_type="associated_vpa"
                    ))
                
        return relationships
