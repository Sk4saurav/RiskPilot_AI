from . import BaseInvestigator
from ..schemas import InvestigationFact, InvestigatorResult
from ..intelligence.base import NetworkIntelligenceProvider
from ..intelligence.ip_provider import LiveIPProvider

class NetworkInvestigator(BaseInvestigator):
    name = "network"
    
    def __init__(self, provider: NetworkIntelligenceProvider = None):
        # Default to Live if none provided (e.g. for standard worker)
        self.provider = provider or LiveIPProvider()
    
    async def investigate(self, event_payload: dict, context: dict) -> InvestigatorResult:
        facts = []
        network = event_payload.get("network", {})
        ip_address = network.get("ip_address") or network.get("ip")
        
        if ip_address:
            # Base IP fact
            facts.append(InvestigationFact(
                investigator=self.name,
                fact_type="NETWORK_IP_SEEN",
                value={"ip": ip_address},
                source="network"
            ))
            
            # Fetch intelligence via Adapter
            intel = await self.provider.lookup_ip(ip_address)
            
            if intel:
                facts.append(InvestigationFact(
                    investigator=self.name,
                    fact_type="NETWORK_INTELLIGENCE",
                    value=intel,
                    source=intel.get("source", "intelligence_provider")
                ))
            else:
                # Fallback fact if external intel fails or returns None
                facts.append(InvestigationFact(
                    investigator=self.name,
                    fact_type="NETWORK_INTELLIGENCE_FAILED",
                    value={"ip": ip_address, "reason": "Provider unavailable"},
                    source="network"
                ))
                
        return InvestigatorResult(investigator_name=self.name, facts=facts)

