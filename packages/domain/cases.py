from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship

from .base import Base
from .audit import AuditTrail

class RiskCase(Base):
    __tablename__ = 'risk_cases'
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    event_id = Column(String, ForeignKey('events.id'))
    status = Column(String, default="NEW") # NEW, INVESTIGATING, PENDING_REVIEW, ESCALATED, RESOLVED, FALSE_POSITIVE, MANUAL_REVIEW_REQUIRED
    priority = Column(String) # LOW, MEDIUM, HIGH, CRITICAL
    assigned_to = Column(String, ForeignKey('users.id'), nullable=True)
    sla_deadline = Column(DateTime, nullable=True)
    
    # Worker Tracking
    attempt_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    claimed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    worker_id = Column(String, nullable=True)
    
    analyst_review_started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    event = relationship("Event", back_populates="risk_cases")
    investigations = relationship("Investigation", back_populates="risk_case")
    risk_assessment = relationship("RiskAssessment", back_populates="risk_case", uselist=False)
    decisions = relationship("Decision", back_populates="risk_case")
    notes = relationship("CaseNote", back_populates="risk_case", cascade="all, delete-orphan")
    
    # Valid transitions from each state
    VALID_TRANSITIONS = {
        "NEW": ["INVESTIGATING", "PENDING_REVIEW", "RESOLVED"],
        "INVESTIGATING": ["PENDING_REVIEW", "MANUAL_REVIEW_REQUIRED", "NEW"], # NEW for retry/stale recovery
        "PENDING_REVIEW": ["ESCALATED", "RESOLVED", "FALSE_POSITIVE"],
        "ESCALATED": ["PENDING_REVIEW"],
        "RESOLVED": [],
        "FALSE_POSITIVE": [],
        "MANUAL_REVIEW_REQUIRED": ["INVESTIGATING", "RESOLVED", "FALSE_POSITIVE", "ESCALATED"]
    }
    
    def transition_to(self, new_status, session, user_id=None):
        """
        Transition the case to a new status and create an audit event.
        Raises ValueError if the transition is invalid.
        """
        if new_status not in self.VALID_TRANSITIONS.get(self.status, []):
            raise ValueError(f"Invalid transition from {self.status} to {new_status}")
            
        old_status = self.status
        self.status = new_status
        
        # Create audit event
        audit_event = AuditTrail(
            id=f"audit_{datetime.utcnow().timestamp()}",
            entity_type="RiskCase",
            entity_id=self.id,
            action=f"TRANSITION_{old_status}_TO_{new_status}",
            user_id=user_id,
            metadata_json={"old_status": old_status, "new_status": new_status}
        )
        session.add(audit_event)

class Investigation(Base):
    __tablename__ = 'investigations'
    id = Column(String, primary_key=True)
    risk_case_id = Column(String, ForeignKey('risk_cases.id'))
    status = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    risk_case = relationship("RiskCase", back_populates="investigations")
    evidence = relationship("Evidence", back_populates="investigation")

class Decision(Base):
    __tablename__ = 'decisions'
    id = Column(String, primary_key=True)
    risk_case_id = Column(String, ForeignKey('risk_cases.id'))
    assessment_id = Column(String, ForeignKey('risk_assessments.id'), nullable=True)
    actor_id = Column(String, ForeignKey('users.id'))
    
    analyst_decision = Column(String)
    is_override = Column(Integer, default=0) # boolean via Integer
    override_reason = Column(Text, nullable=True)
    missing_evidence = Column(Text, nullable=True) # JSON array serialized as string
    
    created_at = Column(DateTime, default=datetime.utcnow)

    risk_case = relationship("RiskCase", back_populates="decisions")
    assessment = relationship("RiskAssessment")
