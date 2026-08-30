import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from apps.api.app.database import get_db
from apps.api.app.auth import get_current_organization
from packages.domain.risk import Policy
from packages.schemas.policies import PolicyCreate, PolicyUpdate, PolicyResponse

router = APIRouter(
    prefix="/v1/policies",
    tags=["Policies"],
)

@router.post("", response_model=PolicyResponse)
async def create_policy(
    policy_data: PolicyCreate, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    policy_id = f"pol_{uuid.uuid4().hex[:12]}"
    
    new_policy = Policy(
        id=policy_id,
        organization_id=org_id,
        name=policy_data.name,
        version=1,
        rules_config=policy_data.rules_config,
        thresholds=policy_data.thresholds,
        is_active=policy_data.is_active
    )
    
    db.add(new_policy)
    await db.commit()
    await db.refresh(new_policy)
    return new_policy

@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    active_only: bool = True, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    stmt = select(Policy).where(Policy.organization_id == org_id)
    if active_only:
        stmt = stmt.where(Policy.is_active == True)
    
    # Get latest version for each policy name
    stmt = stmt.order_by(Policy.name, desc(Policy.version))
    
    result = await db.execute(stmt)
    policies = result.scalars().all()
    
    return policies

@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str, 
    policy_data: PolicyUpdate, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    """
    Updating a policy creates a NEW version and archives the old one.
    """
    result = await db.execute(select(Policy).where(Policy.id == policy_id, Policy.organization_id == org_id))
    old_policy = result.scalar_one_or_none()
    
    if not old_policy:
        raise HTTPException(status_code=404, detail="Policy not found")
        
    if not old_policy.is_active:
        raise HTTPException(status_code=400, detail="Cannot update an inactive policy version")

    # Deactivate old policy
    old_policy.is_active = False
    
    # Create new policy version
    new_policy_id = f"pol_{uuid.uuid4().hex[:12]}"
    new_policy = Policy(
        id=new_policy_id,
        organization_id=org_id,
        name=policy_data.name,
        version=old_policy.version + 1,
        rules_config=policy_data.rules_config,
        thresholds=policy_data.thresholds,
        is_active=policy_data.is_active
    )
    
    db.add(new_policy)
    await db.commit()
    await db.refresh(new_policy)
    
    return new_policy
