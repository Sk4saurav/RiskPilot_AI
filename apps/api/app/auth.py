import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from packages.domain.tenant import ApiKey, User, OrganizationMembership
from .database import get_db

SECRET_KEY = "your-secret-key-keep-it-safe"  # In production, use env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_api_key_record(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    key_hash = hash_api_key(token)
    
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key_record = result.scalar_one_or_none()
    
    if not api_key_record or api_key_record.revoked_at is not None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or revoked API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key_record

async def get_api_key_organization(
    api_key: ApiKey = Depends(get_api_key_record)
) -> str:
    return api_key.organization_id

async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db)
):
    import traceback
    print("get_authenticated_user CALLED!")
    traceback.print_stack()
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
        
    return user

async def get_user_organization(
    user: User = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db)
) -> str:
    # For now, just grab the first organization membership the user has
    result = await db.execute(select(OrganizationMembership).where(OrganizationMembership.user_id == user.id))
    membership = result.scalar_one_or_none()
    
    if not membership:
        raise HTTPException(status_code=403, detail="User does not belong to any organization")
        
    return membership.organization_id

async def get_current_organization(
    org_id: str = Depends(get_user_organization)
) -> str:
    return org_id
