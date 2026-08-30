from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class PolicyBase(BaseModel):
    name: str
    rules_config: Dict[str, Any]
    thresholds: Dict[str, Any]
    is_active: bool = True

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(PolicyBase):
    pass

class PolicyResponse(PolicyBase):
    id: str
    organization_id: str
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}
