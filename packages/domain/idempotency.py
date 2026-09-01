from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base

class IdempotencyKey(Base):
    __tablename__ = 'idempotency_keys'
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    idempotency_key = Column(String, nullable=False)
    request_hash = Column(String, nullable=False)
    response_snapshot = Column(JSON, nullable=True) # Will be null while processing, populated when done
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False) # Important for cleaning up old keys

    organization = relationship("Organization")

    __table_args__ = (
        UniqueConstraint('organization_id', 'idempotency_key', name='uq_org_idempotency_key'),
    )
