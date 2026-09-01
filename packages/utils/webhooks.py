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
        
    # Generate Customer-safe payload
    safe_payload = {
        "id": f"wh_evt_{uuid.uuid4().hex[:12]}",
        "type": event_type,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "organization_id": org_id,
        "data": payload
    }
    
    # Store the deterministic JSON string to avoid reserialization differences later
    payload_str = json.dumps(safe_payload, separators=(',', ':'))
    payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        
    for endpoint in endpoints:
        delivery = WebhookDelivery(
            id=f"whd_{uuid.uuid4().hex[:12]}",
            organization_id=org_id,
            endpoint_id=endpoint.id,
            case_id=payload.get("case_id"),
            event_type=event_type,
            event_id=safe_payload["id"],
            payload=safe_payload,
            payload_hash=payload_hash,
            status="PENDING",
            attempt_count=0
        )
        session.add(delivery)
        
    # No HTTP request here! We just added the PENDING outbox records to the session.
    # The caller's db.commit() will save both the Decision and the WebhookDelivery atomically.
