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
