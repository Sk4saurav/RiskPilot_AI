from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DecisionCreate(BaseModel):
    analyst_decision: str # APPROVE, VERIFY, ESCALATE, HOLD
    is_override: bool
    override_reason: Optional[str] = None
    missing_evidence: Optional[str] = None
    actor_id: str

class DecisionResponse(BaseModel):
    id: str
    risk_case_id: str
    assessment_id: Optional[str]
    actor_id: str
    analyst_decision: str
    is_override: bool
    override_reason: Optional[str]
    missing_evidence: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
