from fastapi import Depends, HTTPException
from typing import List

from .auth import get_authenticated_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from packages.domain.tenant import OrganizationMembership, User

ROLE_HIERARCHY = {
    "OWNER": 40,
    "ADMIN": 30,
    "ANALYST": 20,
    "VIEWER": 10
}

class RequireRole:
    """
    Dependency for Role-Based Access Control (RBAC).
    Usage:
    @router.post("/")
    async def create_something(
        org_id: str = Depends(get_current_organization),
        has_permission: bool = Depends(RequireRole("ADMIN"))
    ): ...
    """
    def __init__(self, required_role: str):
        self.required_role = required_role
        self.required_level = ROLE_HIERARCHY.get(required_role, 0)

    async def __call__(
        self,
        user: User = Depends(get_authenticated_user),
        db: AsyncSession = Depends(get_db)
    ) -> bool:
        # For Alpha, we just grab their primary membership
        result = await db.execute(select(OrganizationMembership).where(OrganizationMembership.user_id == user.id))
        membership = result.scalar_one_or_none()
        
        if not membership:
            raise HTTPException(status_code=403, detail="User does not belong to any organization")
            
        user_level = ROLE_HIERARCHY.get(membership.role, 0)
        
        if user_level < self.required_level:
            raise HTTPException(
                status_code=403, 
                detail=f"Insufficient permissions. Requires {self.required_role} role."
            )
            
        return True
