from datetime import datetime
from sqlalchemy import Column, String, DateTime

from .base import Base

class Relationship(Base):
    __tablename__ = 'relationships'
    id = Column(String, primary_key=True)
    source_id = Column(String)
    target_id = Column(String)
    relationship_type = Column(String) # used, from, via
    created_at = Column(DateTime, default=datetime.utcnow)
