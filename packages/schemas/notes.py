from datetime import datetime
from pydantic import BaseModel, Field

class CaseNoteCreate(BaseModel):
    content: str = Field(..., description="The content of the note")

class CaseNoteResponse(BaseModel):
    id: str
    risk_case_id: str
    author_id: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
