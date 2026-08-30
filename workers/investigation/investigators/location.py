from . import BaseInvestigator
from ..schemas import InvestigationFact, InvestigatorResult

class LocationInvestigator(BaseInvestigator):
    name = "location"
    
    async def investigate(self, event_payload: dict, context: dict) -> InvestigatorResult:
        facts = []
        location = event_payload.get("location", {})
        country_code = location.get("country_code")
        if country_code and country_code != "US": # Mocking high risk location
            facts.append(InvestigationFact(
                investigator=self.name,
                fact_type="LOCATION_COUNTRY",
                value={"country": country_code}, 
                source="geoip_lookup"
            ))
        return InvestigatorResult(investigator_name=self.name, facts=facts)
