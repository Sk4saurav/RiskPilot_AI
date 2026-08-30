from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from .base import Base

class AuditTrail(Base):
    __tablename__ = 'audit_trails'
    id = Column(String, primary_key=True)
    entity_type = Column(String) # RiskCase, Policy, User
    entity_id = Column(String)
    action = Column(String)
    user_id = Column(String, ForeignKey('users.id'), nullable=True)
    previous_hash = Column(String)
    hash = Column(String)
    metadata_json = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
