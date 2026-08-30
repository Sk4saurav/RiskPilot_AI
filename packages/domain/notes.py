from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from .base import Base

class CaseNote(Base):
    __tablename__ = 'case_notes'
    id = Column(String, primary_key=True)
    risk_case_id = Column(String, ForeignKey('risk_cases.id'), nullable=False)
    author_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    risk_case = relationship("RiskCase", back_populates="notes")
