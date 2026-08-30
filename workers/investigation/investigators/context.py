from . import BaseInvestigator
from ..schemas import InvestigationFact, InvestigatorResult

class CustomerContextInvestigator(BaseInvestigator):
    name = "customer_context"
    
    async def investigate(self, event_payload: dict, context: dict) -> InvestigatorResult:
        facts = []
        
        # 1. Support Tickets
        support_tickets = context.get("support_tickets", [])
        active_verified_tickets = [t for t in support_tickets if t.get("status") == "verified_by_customer"]
        
        if active_verified_tickets:
            facts.append(InvestigationFact(
                investigator=self.name,
                fact_type="SUPPORT_TICKET_ACTIVE",
                value={
                    "ticket_count": len(active_verified_tickets),
                    "latest_ticket_id": active_verified_tickets[0].get("id")
                },
                source="zendesk_integration"
            ))
            
        # 2. CRM Data (e.g. VIP Status)
        crm_data = context.get("crm_data", {})
        if crm_data.get("is_vip"):
            facts.append(InvestigationFact(
                investigator=self.name,
                fact_type="VIP_ACCOUNT",
                value={
                    "tier": crm_data.get("vip_tier", "STANDARD"),
                    "account_manager": crm_data.get("account_manager")
                },
                source="crm_integration"
            ))
            
        return InvestigatorResult(investigator_name=self.name, facts=facts)
