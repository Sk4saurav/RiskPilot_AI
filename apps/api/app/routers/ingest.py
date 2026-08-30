from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from apps.api.app.database import get_db
from apps.api.app.auth import get_current_organization, get_api_key_organization
from packages.domain import Organization, Event, RiskCase
import uuid
from datetime import datetime
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
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """Canonical RiskPilot ingestion endpoint."""
    existing_event = await db.execute(select(Event).where(
        Event.event_id == payload.event_id,
        Event.organization_id == org_id
    ))
    event_record = existing_event.scalars().first()
    if event_record:
        # Fetch associated case
        case_res = await db.execute(select(RiskCase).where(RiskCase.event_id == event_record.id))
        case_record = case_res.scalars().first()
        return {
            "status": "accepted", 
            "event_id": payload.event_id, 
            "case_id": case_record.id if case_record else None,
            "message": "Duplicate event ignored"
        }

    event = Event(
        id=f"evt_{uuid.uuid4().hex[:12]}",
        event_id=payload.event_id,
        organization_id=org_id,
        source="api",
        external_id=payload.event_id,
        event_type=payload.event_type,
        payload=payload.model_dump(),
        timestamp=datetime.utcnow()
    )
    db.add(event)
    
    case_id = f"case_{uuid.uuid4().hex[:12]}"
    risk_case = RiskCase(
        id=case_id,
        organization_id=org_id,
        event_id=event.id,
        status="NEW",
        created_at=datetime.utcnow()
    )
    db.add(risk_case)
    await db.commit()
    
    return {"status": "accepted", "event_id": payload.event_id, "case_id": case_id}

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
    return await ingest_event(canonical_payload, background_tasks, org_id, db)
