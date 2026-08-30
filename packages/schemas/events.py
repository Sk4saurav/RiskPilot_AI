from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime

class EventIngestRequest(BaseModel):
    event_id: str = Field(..., description="Unique event identifier from the source system")
    source: str = Field(..., description="Source of the event (e.g. 'stripe', 'auth0')")
    external_id: str = Field(..., description="External identifier for the entity (e.g. user id, transaction id)")
    event_type: str = Field(..., description="Type of event")
    occurred_at: str = Field(..., description="When the event occurred")
    subject: Dict[str, str] = Field(..., description="Subject of the event (type, id)")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Raw event payload")

class EventResponse(BaseModel):
    id: str
    event_id: str
    organization_id: str
    source: str
    external_id: str
    event_type: Optional[str]
    payload: Optional[Dict[str, Any]]
    timestamp: datetime
    
    class Config:
        from_attributes = True
