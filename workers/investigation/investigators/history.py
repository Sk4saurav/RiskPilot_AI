from . import BaseInvestigator
from ..schemas import InvestigationFact, InvestigatorResult

class HistoryInvestigator(BaseInvestigator):
    name = "history"
    
    async def investigate(self, event_payload: dict, context: dict) -> InvestigatorResult:
        facts = []
        user_id = event_payload.get("user_id") or event_payload.get("customer_id")
        if user_id:
            facts.append(InvestigationFact(
                investigator=self.name,
                fact_type="ACCOUNT_AGE",
                value={"user_id": user_id, "age_days": 30}, # Mocked
                source="user_database"
            ))
            
        successful_txs = context.get("successful_past_transactions", [])
        if successful_txs:
            from datetime import datetime
            
            # Simple simulation: just count how many we have and how long ago the most recent one was
            last_tx = successful_txs[0]
            try:
                last_tx_time = datetime.fromisoformat(last_tx["timestamp"])
                days_ago = (datetime.utcnow() - last_tx_time).days
            except:
                days_ago = -1
                
            facts.append(InvestigationFact(
                investigator=self.name,
                fact_type="positive_transaction_history",
                value={
                    "successful_matches": len(successful_txs),
                    "last_successful_transaction_days_ago": days_ago,
                    "matching_device": last_tx.get("device", {}).get("is_new") is False,
                    "matching_location": True # simplified
                },
                source="transaction_history"
            ))
        return InvestigatorResult(investigator_name=self.name, facts=facts)
