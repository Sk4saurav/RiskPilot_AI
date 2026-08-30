import uuid
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.domain.webhooks import WebhookEndpoint, WebhookDelivery

import json
import hmac
import hashlib

async def dispatch_webhook(session: AsyncSession, org_id: str, event_type: str, payload: dict):
    # Find active endpoints for the org
    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.organization_id == org_id,
        WebhookEndpoint.is_active == True
    )
    endpoints = (await session.execute(stmt)).scalars().all()
    
    if not endpoints:
        return
        
    # Generate Customer-safe payload (remove internal fields)
    safe_payload = {
        "id": f"wh_evt_{uuid.uuid4().hex[:12]}",
        "type": event_type,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "organization_id": org_id,
        "data": payload
    }
    
    payload_str = json.dumps(safe_payload, separators=(',', ':'))
        
    async with httpx.AsyncClient() as client:
        for endpoint in endpoints:
            # Generate HMAC signature
            signature = hmac.new(
                endpoint.secret.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            delivery = WebhookDelivery(
                id=f"whd_{uuid.uuid4().hex[:12]}",
                endpoint_id=endpoint.id,
                event_type=event_type,
                event_id=safe_payload["id"],
                payload=safe_payload
            )
            session.add(delivery)
            
            try:
                # In synchronous mode for the first attempt
                response = await client.post(
                    endpoint.url, 
                    content=payload_str,
                    headers={
                        "Content-Type": "application/json",
                        "X-RiskPilot-Event": event_type,
                        "X-RiskPilot-Signature": signature
                    },
                    timeout=5.0
                )
                delivery.status_code = str(response.status_code)
                delivery.is_successful = 200 <= response.status_code < 300
                if delivery.is_successful:
                    delivery.delivered_at = datetime.utcnow()
                else:
                    delivery.last_error = response.text
                    # Schedule retry
                    from datetime import timedelta
                    delivery.next_retry_at = datetime.utcnow() + timedelta(minutes=1)
            except Exception as e:
                delivery.status_code = "ERROR"
                delivery.is_successful = False
                delivery.last_error = str(e)
                from datetime import timedelta
                delivery.next_retry_at = datetime.utcnow() + timedelta(minutes=1)
                
            # We don't commit here, we rely on the caller to commit the transaction
