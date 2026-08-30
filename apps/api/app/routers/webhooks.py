import uuid
import secrets
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.database import get_db
from apps.api.app.auth import get_current_organization
from packages.domain.webhooks import WebhookEndpoint
from packages.schemas.webhooks import WebhookEndpointCreate, WebhookEndpointResponse, WebhookEndpointCreateResponse

router = APIRouter(
    prefix="/v1/webhooks",
    tags=["Webhooks"],
)

@router.post("/endpoints", response_model=WebhookEndpointCreateResponse, summary="Create Webhook Endpoint")
async def create_webhook_endpoint(
    request: WebhookEndpointCreate,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # Generate a secure signing secret
    signing_secret = f"whsec_{secrets.token_hex(16)}"
    
    endpoint = WebhookEndpoint(
        id=f"whep_{uuid.uuid4().hex[:12]}",
        organization_id=org_id,
        url=request.url,
        secret=signing_secret,
        is_active=True
    )
    
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    
    return endpoint

@router.get("/endpoints", response_model=List[WebhookEndpointResponse], summary="List Webhook Endpoints")
async def list_webhook_endpoints(
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    stmt = select(WebhookEndpoint).where(
        WebhookEndpoint.organization_id == org_id,
        WebhookEndpoint.is_active == True
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.delete("/endpoints/{endpoint_id}", summary="Delete Webhook Endpoint")
async def delete_webhook_endpoint(
    endpoint_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    result = await db.execute(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == endpoint_id,
            WebhookEndpoint.organization_id == org_id
        )
    )
    endpoint = result.scalar_one_or_none()
    
    if not endpoint:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found")
        
    endpoint.is_active = False
    await db.commit()
    return {"status": "success", "message": "Endpoint deleted"}
