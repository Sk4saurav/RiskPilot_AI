from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text, JSON, Integer
from sqlalchemy.orm import relationship

from .base import Base

class WebhookEndpoint(Base):
    __tablename__ = 'webhook_endpoints'
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    url = Column(String, nullable=False)
    secret = Column(String, nullable=False) # For signing payload
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")

class WebhookDelivery(Base):
    __tablename__ = 'webhook_deliveries'
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    endpoint_id = Column(String, ForeignKey('webhook_endpoints.id'), nullable=False)
    case_id = Column(String, ForeignKey('risk_cases.id'), nullable=True)
    event_type = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    payload_hash = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, DELIVERING, RETRY_WAIT, DELIVERED, FAILED
    status_code = Column(String, nullable=True)
    
    # Retry logic
    attempt_count = Column(Integer, default=1)
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    endpoint = relationship("WebhookEndpoint")
    organization = relationship("Organization")
    case = relationship("RiskCase")
