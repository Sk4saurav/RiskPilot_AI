from datetime import datetime
from . import BaseInvestigator
from ..schemas import InvestigationFact, InvestigatorResult
from .repositories import UPIHistoryRepository

class UPIInvestigator(BaseInvestigator):
    name = "upi"
    
    def __init__(self, repository: UPIHistoryRepository, config: dict = None):
        self.repository = repository
        self.config = config or {}
        # Make threshold configurable, default to 3
        self.distinct_vpa_threshold = self.config.get("distinct_vpa_threshold", 3)
        self.window_minutes = self.config.get("window_minutes", 60)
        
    async def investigate(self, event_payload: dict, context: dict) -> InvestigatorResult:
        facts = []
        
        # Extract fields
        device_id = event_payload.get("device", {}).get("id") or event_payload.get("device_id")
        vpa = event_payload.get("transaction", {}).get("vpa") or event_payload.get("vpa")
        
        if not device_id or not vpa:
            return InvestigatorResult(investigator_name=self.name, facts=facts)
            
        org_id = context.get("org_id")
        event_timestamp = context.get("event_timestamp")
        
        if not org_id or not event_timestamp:
            # Need organization isolation and deterministic time to query
            return InvestigatorResult(investigator_name=self.name, facts=facts)
            
        # 1. Fetch recent distinct VPAs for this device
        recent_vpas = await self.repository.get_recent_vpas(
            org_id=org_id,
            device_id=device_id,
            event_timestamp=event_timestamp,
            window_minutes=self.window_minutes
        )
        
        distinct_count = len(recent_vpas)
        
        # Emit velocity fact
        facts.append(InvestigationFact(
            investigator=self.name,
            fact_type="upi_velocity",
            value={
                "device_id": device_id,
                "distinct_vpas": distinct_count,
                "vpa_list": recent_vpas,
                "window_minutes": self.window_minutes
            },
            source="event_history"
        ))
        
        # If threshold crossed, emit the abuse ring fact
        if distinct_count >= self.distinct_vpa_threshold:
            facts.append(InvestigationFact(
                investigator=self.name,
                fact_type="upi_abuse_ring",
                value={
                    "device_id": device_id,
                    "distinct_vpas": distinct_count,
                    "vpa_list": recent_vpas,
                    "threshold": self.distinct_vpa_threshold
                },
                source="event_history"
            ))
            
        return InvestigatorResult(investigator_name=self.name, facts=facts)
