from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .events import EventResponse

class RiskCaseResponse(BaseModel):
    id: str
    event_id: str
    status: str
    priority: Optional[str]
    assigned_to: Optional[str]
    created_at: datetime
    
    event: Optional[EventResponse] = None
    
    class Config:
        from_attributes = True

class IngestResponse(BaseModel):
    event: EventResponse
    case: RiskCaseResponse
    is_new: bool
