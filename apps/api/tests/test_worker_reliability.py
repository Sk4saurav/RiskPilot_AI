import pytest
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from packages.domain.base import Base
from packages.domain.cases import RiskCase
from packages.domain.tenant import Organization
from workers.investigation.claim import claim_new_case, recover_stale_claims

# We use in-memory SQLite for tests to run them quickly.
# The SKIP LOCKED Postgres-specific behavior is mocked/fallback-ed in claim.py for sqlite.
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def session():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        # Create a mock org
        org = Organization(id="org_test", name="Test Org", api_key_hash="hash")
        session.add(org)
        await session.commit()
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_worker_crash_recovery(session: AsyncSession):
    # Setup a stale case
    stale_time = datetime.utcnow() - timedelta(minutes=15)
    case = RiskCase(id="case_1", organization_id="org_test", status="INVESTIGATING", claimed_at=stale_time, attempt_count=1)
    session.add(case)
    await session.commit()
    
    # Recover
    recovered = await recover_stale_claims(session, timeout_minutes=10)
    assert recovered == 1
    
    await session.refresh(case)
    assert case.status == "NEW"
    assert case.last_error == "Worker stale timeout"

@pytest.mark.asyncio
async def test_max_retries_exceeded(session: AsyncSession):
    # Setup a stale case that has already been attempted 3 times
    stale_time = datetime.utcnow() - timedelta(minutes=15)
    case = RiskCase(id="case_2", organization_id="org_test", status="INVESTIGATING", claimed_at=stale_time, attempt_count=3)
    session.add(case)
    await session.commit()
    
    # Recover
    recovered = await recover_stale_claims(session, timeout_minutes=10)
    assert recovered == 1
    
    await session.refresh(case)
    assert case.status == "MANUAL_REVIEW_REQUIRED"

@pytest.mark.asyncio
async def test_concurrent_claiming_simulation(session: AsyncSession):
    # Add a new case
    case = RiskCase(id="case_3", organization_id="org_test", status="NEW")
    session.add(case)
    await session.commit()
    
    # Worker 1 claims
    case_id_w1 = await claim_new_case(session, "worker_1")
    assert case_id_w1 == "case_3"
    
    # Worker 2 attempts to claim
    case_id_w2 = await claim_new_case(session, "worker_2")
    assert case_id_w2 is None # No NEW cases available
