from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index

from .base import Base

class EventHistory(Base):
    """
    Normalized, fast-lookup table for event history querying.
    Used by investigators to query historical events without parsing large JSON payloads.
    """
    __tablename__ = 'event_history'
    
    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey('events.id'), nullable=False)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Optional fields extracted from the event payload for fast querying
    device_id = Column(String, nullable=True)
    vpa = Column(String, nullable=True)
    customer_id = Column(String, nullable=True)
    
    __table_args__ = (
        Index('idx_event_history_org_device_time', 'organization_id', 'device_id', 'timestamp'),
        Index('idx_event_history_org_vpa_time', 'organization_id', 'vpa', 'timestamp'),
    )
