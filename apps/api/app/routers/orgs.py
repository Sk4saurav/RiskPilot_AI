import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from apps.api.app.database import get_db
from apps.api.app.auth import hash_api_key
from packages.domain.tenant import Organization, ApiKey

router = APIRouter(
    prefix="/v1/orgs",
    tags=["Organizations"],
)

class OrgCreate(BaseModel):
    name: str

class OrgResponse(BaseModel):
    id: str
    name: str

class ApiKeyCreateResponse(BaseModel):
    id: str
    key: str # The raw key, only shown once!
    prefix: str

@router.post("", response_model=OrgResponse)
async def create_organization(payload: OrgCreate, db: AsyncSession = Depends(get_db)):
    org_id = f"org_{uuid.uuid4().hex[:12]}"
    new_org = Organization(
        id=org_id,
        name=payload.name
    )
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)
    
    return new_org

@router.post("/{org_id}/apikeys", response_model=ApiKeyCreateResponse)
async def create_api_key(org_id: str, db: AsyncSession = Depends(get_db)):
    # Verify org exists
    org_res = await db.execute(select(Organization).where(Organization.id == org_id))
    if not org_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Organization not found")
        
    raw_secret = secrets.token_urlsafe(32)
    # The actual prefix should include the first 4 chars of the secret so we can show them
    prefix = f"rp_live_{raw_secret[:4]}"
    full_key = f"rp_live_{raw_secret}"
    
    key_hash = hash_api_key(full_key)
    
    key_id = f"key_{uuid.uuid4().hex[:12]}"
    api_key = ApiKey(
        id=key_id,
        organization_id=org_id,
        name="Production Key",
        key_hash=key_hash,
        prefix=prefix
    )
    db.add(api_key)
    await db.commit()
    
    return {
        "id": key_id,
        "key": full_key,
        "prefix": prefix
    }

class ApiKeyListResponse(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: str
    revoked_at: str | None

@router.get("/{org_id}/apikeys", response_model=list[ApiKeyListResponse])
async def list_api_keys(org_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiKey).where(ApiKey.organization_id == org_id).order_by(ApiKey.created_at.desc()))
    keys = result.scalars().all()
    
    return [
        {
            "id": k.id,
            "name": k.name,
            "prefix": k.prefix,
            "created_at": k.created_at.isoformat(),
            "revoked_at": k.revoked_at.isoformat() if k.revoked_at else None
        } for k in keys
    ]

@router.delete("/{org_id}/apikeys/{key_id}")
async def revoke_api_key(org_id: str, key_id: str, db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.organization_id == org_id))
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    key.revoked_at = datetime.utcnow()
    await db.commit()
    return {"status": "revoked"}

