from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Boolean, JSON
from sqlalchemy.orm import relationship

from .base import Base

class ReplayDataset(Base):
    __tablename__ = 'validation_replay_datasets'
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey('organizations.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    events = relationship("ReplayEvent", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("ReplayRun", back_populates="dataset", cascade="all, delete-orphan")

class ReplayEvent(Base):
    """Stores the historical ground truth, separate from RiskPilot ingestion."""
    __tablename__ = 'validation_replay_events'
    
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey('validation_replay_datasets.id'), nullable=False)
    
    customer_event_id = Column(String, nullable=False)
    original_timestamp = Column(DateTime, nullable=True)
    
    # The normalized event payload ready to be fed into the investigation logic
    normalized_event = Column(JSON, nullable=False)
    
    # Deterministic context for the replay
    historical_context_snapshot = Column(JSON, nullable=True)
    
    # Historical ground truth
    manual_investigation_time_sec = Column(Integer, nullable=True)
    manual_analyst_time_sec = Column(Integer, nullable=True)
    manual_decision = Column(String, nullable=True)
    manual_evidence_sources = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    dataset = relationship("ReplayDataset", back_populates="events")
    results = relationship("ValidationResult", back_populates="event", cascade="all, delete-orphan")

class ReplayRun(Base):
    __tablename__ = 'validation_replay_runs'
    
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey('validation_replay_datasets.id'), nullable=False)
    status = Column(String, default="RUNNING") # RUNNING, COMPLETED, FAILED
    
    # Versioning & Reproducibility Context
    policy_version = Column(Integer, nullable=True)
    engine_version = Column(String, default="v0.1.0")
    investigator_version = Column(String, default="v1.0.0")
    configuration_snapshot = Column(JSON, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    dataset = relationship("ReplayDataset", back_populates="runs")
    results = relationship("ValidationResult", back_populates="run", cascade="all, delete-orphan")

class ValidationResult(Base):
    __tablename__ = 'validation_results'
    
    id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey('validation_replay_runs.id'), nullable=False)
    event_id = Column(String, ForeignKey('validation_replay_events.id'), nullable=False)
    
    # RiskPilot Execution Metrics
    riskpilot_investigation_time_sec = Column(Integer, nullable=True)
    riskpilot_analyst_time_sec = Column(Integer, nullable=True) # Simulated
    
    # Outcomes
    riskpilot_recommendation = Column(String, nullable=True)
    riskpilot_decision = Column(String, nullable=True) # Usually matches recommendation if auto, or simulated
    riskpilot_score = Column(Float, nullable=True)
    
    # Reproducibility Snapshots
    evidence_snapshot = Column(JSON, nullable=True)
    signals_snapshot = Column(JSON, nullable=True)
    
    # Evidence Validation
    evidence_coverage_percent = Column(Float, nullable=True)
    
    # Derived Metrics (Case-level Audit)
    time_saved_sec = Column(Integer, nullable=True)
    time_saved_percent = Column(Float, nullable=True)
    decision_match = Column(Boolean, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("ReplayRun", back_populates="results")
    event = relationship("ReplayEvent", back_populates="results")
