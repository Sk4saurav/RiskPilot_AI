from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Text, JSON, Integer
from sqlalchemy.orm import relationship

from .base import Base

class Evidence(Base):
    __tablename__ = 'evidence'
    id = Column(String, primary_key=True)
    investigation_id = Column(String, ForeignKey('investigations.id'))
    evidence_type = Column(String)
    source = Column(String)
    severity = Column(String)
    weight = Column(Integer, default=0)
    confidence = Column(Float)
    value = Column(JSON)
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="evidence")
