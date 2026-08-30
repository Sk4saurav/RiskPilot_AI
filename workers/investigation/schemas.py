from pydantic import BaseModel, Field
from typing import Dict, Any, List

class InvestigationFact(BaseModel):
    investigator: str
    fact_type: str
    value: Dict[str, Any]
    confidence: float = 1.0
    source: str

class InvestigatorResult(BaseModel):
    investigator_name: str
    facts: List[InvestigationFact] = Field(default_factory=list)
