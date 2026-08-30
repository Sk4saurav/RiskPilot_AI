import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from apps.api.app.database import get_db
from apps.api.app.auth import get_current_organization
from packages.domain import RiskCase, Investigation, Evidence, RiskAssessment, AuditTrail, Relationship

router = APIRouter(
    prefix="/v1/cases",
    tags=["Copilot"],
)

import json
from typing import List, Optional
from pydantic import BaseModel, Field
from apps.api.app.config import settings

class CopilotQuery(BaseModel):
    query: str

class CopilotResponse(BaseModel):
    answer: str
    evidence_references: List[str]
    confidence: float
    limitations: List[str]
    context_used: dict

@router.post("/{case_id}/copilot/ask", response_model=CopilotResponse)
async def ask_copilot(
    case_id: str, 
    payload: CopilotQuery, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # 1. Fetch all case context
    case_res = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = case_res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    assessment_res = await db.execute(select(RiskAssessment).where(RiskAssessment.risk_case_id == case_id))
    assessment = assessment_res.scalar_one_or_none()
    
    inv_res = await db.execute(select(Investigation).where(Investigation.risk_case_id == case_id))
    investigations = inv_res.scalars().all()
    
    evidence_list = []
    if investigations:
        inv_ids = [i.id for i in investigations]
        ev_res = await db.execute(select(Evidence).where(Evidence.investigation_id.in_(inv_ids)))
        evidence_list = ev_res.scalars().all()
        
    audit_res = await db.execute(select(AuditTrail).where(AuditTrail.entity_type == "RiskCase", AuditTrail.entity_id == case_id))
    audits = audit_res.scalars().all()
    
    # 2. Build structured context payload
    context = {
        "case_id": case.id,
        "status": case.status,
        "priority": case.priority,
        "assessment": {
            "score": assessment.risk_score if assessment else None,
            "recommendation": assessment.recommendation if assessment else None,
            "policy_version": assessment.policy_version if assessment else None
        },
        "evidence": [
            {
                "id": e.id,
                "type": e.evidence_type,
                "source": e.source,
                "severity": e.severity,
                "weight": e.weight
            } for e in evidence_list
        ],
        "timeline_events": [a.action for a in audits]
    }
    
    # 3. Call LLM (Fallback mock for alpha)
    response_data = {
        "answer": "",
        "evidence_references": [],
        "confidence": 0.0,
        "limitations": ["No external threat-intelligence source was available."]
    }
    
    prompt = f"""
    Context: {json.dumps(context)}
    User asks: {payload.query}
    
    Respond in strict JSON matching this schema:
    {{
      "answer": "...",
      "evidence_references": ["ev_123", "ev_456"],
      "confidence": 0.95,
      "limitations": ["string"]
    }}
    """
    
    try:
        import openai
        if settings.openai_api_key:
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            resp = await client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {"role": "system", "content": "You are an AI analyst. Always return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            llm_text = resp.choices[0].message.content
            response_data = json.loads(llm_text)
        else:
            raise ImportError
    except (ImportError, Exception):
        # Deterministic Fallback 
        evidence_summary = ", ".join([f"{e['type']} (+{e['weight']})" for e in context['evidence']])
        evidence_ids = [e['id'] for e in context['evidence']]
        
        response_data = {
            "answer": (f"This is a simulated AI Copilot response. "
                       f"Based on the context, the case scored {context['assessment']['score']} "
                       f"primarily due to: {evidence_summary}."),
            "evidence_references": evidence_ids,
            "confidence": 0.85,
            "limitations": ["LLM provider is unavailable. Serving deterministic fallback."]
        }
                         
    return CopilotResponse(
        answer=response_data.get("answer", ""),
        evidence_references=response_data.get("evidence_references", []),
        confidence=response_data.get("confidence", 0.0),
        limitations=response_data.get("limitations", []),
        context_used=context
    )
