from . import BaseInvestigator
from ..schemas import InvestigationFact, InvestigatorResult

class TransactionInvestigator(BaseInvestigator):
    name = "transaction"
    
    async def investigate(self, event_payload: dict, context: dict) -> InvestigatorResult:
        facts = []
        
        amount_cents = event_payload.get("amount_cents")
        if amount_cents and amount_cents > 1000000: # High Amount
            facts.append(InvestigationFact(
                investigator=self.name,
                fact_type="TRANSACTION_AMOUNT",
                value={"amount": amount_cents},
                source="transaction_payload"
            ))
            
        return InvestigatorResult(investigator_name=self.name, facts=facts)
