from ..schemas import InvestigationFact, InvestigatorResult

class BaseInvestigator:
    name: str = "base"
    
    async def investigate(self, event_payload: dict, context: dict) -> InvestigatorResult:
        raise NotImplementedError
