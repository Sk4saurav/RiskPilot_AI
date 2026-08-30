import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from packages.domain.cases import RiskCase

async def claim_new_case(session: AsyncSession, worker_id: str) -> str | None:
    """
    Attempts to claim a NEW case securely.
    Uses PostgreSQL FOR UPDATE SKIP LOCKED when possible,
    falls back to a standard update pattern for SQLite.
    Returns the case_id if claimed, otherwise None.
    """
    is_sqlite = session.bind.dialect.name == "sqlite"
    print(f"DEBUG: is_sqlite={is_sqlite}, dialect={session.bind.dialect.name}")
    
    if is_sqlite:
        # SQLite doesn't support SKIP LOCKED. 
        # Fallback approach for local single-worker concurrency
        stmt = select(RiskCase).where(RiskCase.status == "NEW").order_by(RiskCase.created_at).limit(1)
        result = await session.execute(stmt)
        case = result.scalar_one_or_none()
        
        if not case:
            return None
            
        case.status = "INVESTIGATING"
        case.worker_id = worker_id
        case.claimed_at = datetime.utcnow()
        case.attempt_count += 1
        await session.commit()
        return case.id
    else:
        # PostgreSQL Production safe approach
        stmt = (
            select(RiskCase.id)
            .where(RiskCase.status == "NEW")
            .order_by(RiskCase.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        
        result = await session.execute(stmt)
        case_id = result.scalar_one_or_none()
        
        if not case_id:
            return None
            
        # Perform the actual claim
        update_stmt = (
            update(RiskCase)
            .where(RiskCase.id == case_id)
            .values(
                status="INVESTIGATING",
                worker_id=worker_id,
                claimed_at=datetime.utcnow(),
                attempt_count=RiskCase.attempt_count + 1
            )
        )
        await session.execute(update_stmt)
        await session.commit()
        return case_id

async def recover_stale_claims(session: AsyncSession, timeout_minutes: int = 10) -> int:
    """
    Find cases stuck in INVESTIGATING longer than the timeout and return them to NEW
    so another worker can retry them.
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
    
    stmt = select(RiskCase).where(RiskCase.status == "INVESTIGATING", RiskCase.claimed_at < cutoff_time)
    result = await session.execute(stmt)
    stale_cases = result.scalars().all()
    
    count = 0
    for case in stale_cases:
        case.last_error = "Worker stale timeout"
        case.worker_id = None
        if case.attempt_count >= 3:
            case.status = "MANUAL_REVIEW_REQUIRED"
        else:
            case.status = "NEW"
        count += 1
        
    if count > 0:
        await session.commit()
    return count
