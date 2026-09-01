import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any, Optional
from apps.api.app.database import get_db
from apps.api.app.auth import get_current_organization, get_api_key_organization
from packages.domain import Organization, Event, RiskCase, IdempotencyKey
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select

router = APIRouter(prefix="/v1", tags=["Ingest"])

class EventPayload(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    actor: dict
    transaction: dict
    network: dict
    device: dict
    location: dict

@router.post("/events/ingest")
async def ingest_event(
    payload: EventPayload,
    background_tasks: BackgroundTasks,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    org_id: str = Depends(get_api_key_organization),
    db: AsyncSession = Depends(get_db)
):
    """Canonical RiskPilot ingestion endpoint with strict concurrency-safe idempotency."""
    
    # 1. Hash the payload to detect modifications
    payload_dict = payload.model_dump()
    payload_str = json.dumps(payload_dict, sort_keys=True)
    request_hash = hashlib.sha256(payload_str.encode()).hexdigest()

    # 2. Try to fetch existing idempotency key
    existing_key_res = await db.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.organization_id == org_id,
            IdempotencyKey.idempotency_key == idempotency_key
        )
    )
    existing_key = existing_key_res.scalar_one_or_none()

    if existing_key:
        if existing_key.request_hash != request_hash:
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT: Payload differs for the same Idempotency-Key")
        if existing_key.response_snapshot:
            return existing_key.response_snapshot
        # If it's still processing, we can return a 202 or wait. 
        # Since our ingest is fast, we will assume it's created if we get here.
        raise HTTPException(status_code=425, detail="Request is currently being processed by another concurrent request")

    # 3. Attempt Atomic Reservation
    idem_record = IdempotencyKey(
        id=f"idem_{uuid.uuid4().hex[:12]}",
        organization_id=org_id,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(idem_record)
    
    try:
        await db.flush() # Try to reserve the key atomically
    except IntegrityError:
        # A concurrent request beat us to it!
        await db.rollback()
        import asyncio
        # Wait for the winner to commit
        winner = None
        for _ in range(15): # wait up to 1.5 seconds
            winner_res = await db.execute(
                select(IdempotencyKey).where(
                    IdempotencyKey.organization_id == org_id,
                    IdempotencyKey.idempotency_key == idempotency_key
                )
            )
            winner = winner_res.scalar_one_or_none()
            if winner:
                break
            await asyncio.sleep(0.1)
            
        if not winner:
            raise HTTPException(status_code=500, detail="IDEMPOTENCY_CONFLICT: Concurrent request failed to commit")
            
        if winner.request_hash != request_hash:
            raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT: Payload differs for the same Idempotency-Key")
        
        # If we caught them mid-flight, return 425
        if not winner.response_snapshot:
             raise HTTPException(status_code=425, detail="Request is currently being processed by a concurrent request")
             
        return winner.response_snapshot
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

    # 4. Proceed with core ingestion logic
    existing_event = await db.execute(select(Event).where(
        Event.event_id == payload.event_id,
        Event.organization_id == org_id
    ))
    event_record = existing_event.scalars().first()
    
    if event_record:
        # Fetch associated case
        case_res = await db.execute(select(RiskCase).where(RiskCase.event_id == event_record.id))
        case_record = case_res.scalars().first()
        response = {
            "status": "accepted", 
            "event_id": payload.event_id, 
            "case_id": case_record.id if case_record else None,
            "message": "Duplicate event ignored"
        }
    else:
        event = Event(
            id=f"evt_{uuid.uuid4().hex[:12]}",
            event_id=payload.event_id,
            organization_id=org_id,
            source="api",
            external_id=payload.event_id,
            event_type=payload.event_type,
            payload=payload_dict,
            timestamp=datetime.utcnow()
        )
        db.add(event)
        
        from packages.domain.history import EventHistory
        # Extract fields safely from payload dictionary
        device_id = payload_dict.get("device", {}).get("id") or payload_dict.get("device_id")
        vpa = payload_dict.get("transaction", {}).get("vpa") or payload_dict.get("vpa")
        customer_id = payload_dict.get("actor", {}).get("user_id") or payload_dict.get("customer_id")
        
        history_record = EventHistory(
            id=f"evh_{uuid.uuid4().hex[:12]}",
            event_id=event.id,
            organization_id=org_id,
            timestamp=event.timestamp,
            device_id=device_id,
            vpa=vpa,
            customer_id=customer_id
        )
        db.add(history_record)
        
        case_id = f"case_{uuid.uuid4().hex[:12]}"
        risk_case = RiskCase(
            id=case_id,
            organization_id=org_id,
            event_id=event.id,
            status="NEW",
            created_at=datetime.utcnow()
        )
        db.add(risk_case)
        response = {"status": "accepted", "event_id": payload.event_id, "case_id": case_id}

    # 5. Snapshot the response and save
    idem_record.response_snapshot = response
    await db.commit()
    
    return response

class DesignPartnerAdapterV1(BaseModel):
    """
    Temporary Beta schema for the Design Partner Trial.
    Translates directly to the internal canonical Event format.
    """
    customer_event_id: str
    timestamp: str
    customer_id: str
    tx_amount: int
    currency: str
    ip: str
    country_code: str
    city: str
    device_is_new: bool

@router.post("/integrations/{integration}/events")
async def ingest_integration_event(
    integration: str,
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    org_id: str = Depends(get_api_key_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Adapter endpoint for specific customer integrations.
    """
    if integration != "design_partner":
        raise HTTPException(status_code=404, detail="Integration not found")
        
    try:
        # Validate against temporary schema
        adapter_payload = DesignPartnerAdapterV1(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid integration payload: {str(e)}")
        
    # Map to Canonical RiskPilot Event
    canonical_payload = EventPayload(
        event_id=adapter_payload.customer_event_id,
        event_type="transaction",
        timestamp=adapter_payload.timestamp,
        actor={
            "user_id": adapter_payload.customer_id
        },
        transaction={
            "amount_cents": adapter_payload.tx_amount,
            "currency": adapter_payload.currency
        },
        network={
            "ip": adapter_payload.ip
        },
        device={
            "is_new": adapter_payload.device_is_new
        },
        location={
            "country": adapter_payload.country_code,
            "city": adapter_payload.city
        }
    )
    
    # Delegate to the existing canonical ingestion logic
    return await ingest_event(canonical_payload, background_tasks, idempotency_key, org_id, db)
