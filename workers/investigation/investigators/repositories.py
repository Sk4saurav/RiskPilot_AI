from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from packages.domain.history import EventHistory

class UPIHistoryRepository(ABC):
    """
    Provides read-only access to historical events for UPI investigations.
    """
    @abstractmethod
    async def get_recent_vpas(self, org_id: str, device_id: str, event_timestamp: datetime, window_minutes: int) -> List[str]:
        """
        Retrieves all distinct VPAs associated with a device in the given time window leading up to (and including) the event_timestamp.
        """
        pass

class SQLAlchemyUPIHistoryRepository(UPIHistoryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_recent_vpas(self, org_id: str, device_id: str, event_timestamp: datetime, window_minutes: int) -> List[str]:
        window_start = event_timestamp - timedelta(minutes=window_minutes)
        
        # Query the normalized event history table
        stmt = select(EventHistory.vpa).where(
            EventHistory.organization_id == org_id,
            EventHistory.device_id == device_id,
            EventHistory.vpa.isnot(None),
            EventHistory.timestamp >= window_start,
            EventHistory.timestamp <= event_timestamp
        )
        
        result = await self.session.execute(stmt)
        # Return distinct VPAs
        vpas = result.scalars().all()
        return list(set(vpas))
