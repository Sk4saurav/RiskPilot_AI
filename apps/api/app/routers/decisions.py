import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.database import get_db
from apps.api.app.auth import get_current_organization
from packages.domain import RiskCase, Decision, RiskAssessment, AuditTrail
from packages.schemas.decisions import DecisionCreate, DecisionResponse

router = APIRouter(
    prefix="/v1/cases",
    tags=["Decisions"],
)

@router.post("/{case_id}/decisions", response_model=DecisionResponse)
async def submit_decision(
    case_id: str, 
    decision_data: DecisionCreate, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # 1. Fetch Case and verify ownership
    result = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # 2. Fetch Risk Assessment to link
    assessment_result = await db.execute(select(RiskAssessment).where(RiskAssessment.risk_case_id == case_id))
    assessment = assessment_result.scalar_one_or_none()
    
    assessment_id = assessment.id if assessment else None
    
    # 3. Create Decision record
    decision_id = f"dec_{uuid.uuid4().hex[:12]}"
    new_decision = Decision(
        id=decision_id,
        risk_case_id=case_id,
        assessment_id=assessment_id,
        actor_id=decision_data.actor_id,
        analyst_decision=decision_data.analyst_decision,
        is_override=1 if decision_data.is_override else 0,
        override_reason=decision_data.override_reason,
        missing_evidence=decision_data.missing_evidence
    )
    
    db.add(new_decision)
    
    # 4. Create Audit Trail
    audit = AuditTrail(
        id=f"audit_{uuid.uuid4().hex[:12]}",
        entity_type="RiskCase",
        entity_id=case_id,
        action="HUMAN_DECISION",
        user_id=decision_data.actor_id,
        metadata_json={
            "analyst_decision": decision_data.analyst_decision,
            "is_override": decision_data.is_override,
            "override_reason": decision_data.override_reason
        }
    )
    db.add(audit)
    
    # 5. Resolve the Case
    new_status = "RESOLVED"
    if decision_data.analyst_decision in ["APPROVE", "HOLD", "VERIFY"]:
        new_status = "RESOLVED"
        case.transition_to(new_status, db, user_id=decision_data.actor_id)
    elif decision_data.analyst_decision == "ESCALATE":
        new_status = "ESCALATED"
        case.transition_to(new_status, db, user_id=decision_data.actor_id)
        
    # 6. Dispatch Webhook
    from packages.utils.webhooks import dispatch_webhook
    await dispatch_webhook(
        session=db, 
        org_id=org_id, 
        event_type="case.resolved",
        payload={
            "case_id": case.id, 
            "status": new_status, 
            "analyst_decision": decision_data.analyst_decision,
            "is_override": decision_data.is_override,
            "override_reason": decision_data.override_reason
        }
    )
        
    await db.commit()
    await db.refresh(new_decision)
    
    return new_decision
