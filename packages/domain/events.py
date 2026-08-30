from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base

class Event(Base):
    __tablename__ = 'events'
    
    # Event IDs must be unique internally.
    id = Column(String, primary_key=True)
    event_id = Column(String, unique=True, nullable=False)
    
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    source = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    
    event_type = Column(String)
    payload = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="events")
    risk_cases = relationship("RiskCase", back_populates="event")
    
    __table_args__ = (
        UniqueConstraint('organization_id', 'source', 'external_id', name='uq_event_org_source_ext'),
    )
