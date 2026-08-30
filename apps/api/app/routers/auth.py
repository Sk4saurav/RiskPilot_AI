import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from apps.api.app.database import get_db
from apps.api.app.auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from packages.domain.tenant import User, Organization, OrganizationMembership

router = APIRouter(
    prefix="/v1/auth",
    tags=["Authentication"],
)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    organization_name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    org_id: str

@router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Create Organization
    org_id = f"org_{uuid.uuid4().hex[:12]}"
    new_org = Organization(
        id=org_id,
        name=user_data.organization_name
    )
    db.add(new_org)
    
    # Create User
    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    new_user = User(
        id=user_id,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(new_user)
    
    # Create Membership
    membership_id = f"mem_{uuid.uuid4().hex[:12]}"
    new_membership = OrganizationMembership(
        id=membership_id,
        user_id=user_id,
        organization_id=org_id,
        role="OWNER"
    )
    db.add(new_membership)
    
    await db.commit()
    
    # Generate Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id, "role": "OWNER", "org": org_id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": user_id, "org_id": org_id}

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=Token)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Get primary org (simplified)
    mem_result = await db.execute(select(OrganizationMembership).where(OrganizationMembership.user_id == user.id))
    membership = mem_result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(status_code=403, detail="User has no organization")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "role": membership.role, "org": membership.organization_id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "org_id": membership.organization_id}
