from . import BaseInvestigator
from ..schemas import InvestigationFact, InvestigatorResult

class DeviceInvestigator(BaseInvestigator):
    name = "device"
    
    async def investigate(self, event_payload: dict, context: dict) -> InvestigatorResult:
        facts = []
        
        device = event_payload.get("device", {})
        
        from apps.api.app.config import settings
        if settings.fingerprintjs_api_key and device.get("device_id"):
            # If they provided a real Server API key, we would query the Fingerprint Server API here.
            # Example: httpx.get(f"https://api.fpjs.io/visitors/{device['device_id']}?api_key={settings.fingerprintjs_api_key}")
            # For this boilerplate, we'll assume it returns first_seen=True for demo simplicity if is_new is true.
            pass
            
        if device.get("is_new"):
            facts.append(InvestigationFact(
                investigator=self.name,
                fact_type="DEVICE_SEEN",
                value={"device_id": device.get("device_id", "simulated"), "first_seen": True},
                source="device_payload"
            ))
            
        return InvestigatorResult(investigator_name=self.name, facts=facts)
