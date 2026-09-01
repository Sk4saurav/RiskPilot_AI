from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class WebhookEndpointCreate(BaseModel):
    url: str

class WebhookEndpointResponse(BaseModel):
    id: str
    url: str
    is_active: bool
    created_at: datetime
    # We do NOT return the secret in the response after creation for security reasons,
    # except maybe right after creation.
    
    class Config:
        from_attributes = True

class WebhookEndpointCreateResponse(WebhookEndpointResponse):
    secret: str # Only returned once during creation

class WebhookDeliveryResponse(BaseModel):
    id: str
    endpoint_id: str
    case_id: Optional[str] = None
    event_type: str
    event_id: str
    payload: dict
    status: str
    status_code: Optional[str] = None
    attempt_count: int
    last_error: Optional[str] = None
    next_retry_at: Optional[datetime] = None
    created_at: datetime
    delivered_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
