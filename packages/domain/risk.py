from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base

class Policy(Base):
    __tablename__ = 'policies'
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'))
    name = Column(String)
    version = Column(Integer, default=1)
    rules_config = Column(JSON) # e.g. weights for different signals
    thresholds = Column(JSON) # e.g. LOW: 0-29, HIGH: 60-79
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="policies")

    __table_args__ = (
        UniqueConstraint('organization_id', 'name', 'version', name='uq_policy_org_name_version'),
    )

class RiskAssessment(Base):
    __tablename__ = 'risk_assessments'
    id = Column(String, primary_key=True)
    risk_case_id = Column(String, ForeignKey('risk_cases.id'))
    
    # Store exact policy version and snapshots
    policy_id = Column(String, ForeignKey('policies.id'))
    policy_version = Column(Integer)
    policy_snapshot = Column(JSON)
    signals_snapshot = Column(JSON)
    
    risk_score = Column(Integer)
    recommendation = Column(String) # HOLD, APPROVE, ESCALATE
    rationale = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    risk_case = relationship("RiskCase", back_populates="risk_assessment")
    policy = relationship("Policy")
