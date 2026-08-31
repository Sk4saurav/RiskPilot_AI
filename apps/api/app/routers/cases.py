from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.database import get_db
from apps.api.app.auth import get_current_organization
from packages.domain import RiskCase, AuditTrail, Evidence, RiskAssessment
from packages.schemas.cases import RiskCaseResponse

router = APIRouter(
    prefix="/v1/cases",
    tags=["Cases"],
)

from typing import List, Optional

@router.get(
    "", 
    response_model=List[RiskCaseResponse],
    summary="List Cases",
    description="Retrieve a list of risk cases for the current organization, optionally filtered, searched, and sorted."
)
async def list_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_desc: Optional[bool] = True,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    from sqlalchemy.orm import selectinload
    stmt = select(RiskCase).where(RiskCase.organization_id == org_id).options(selectinload(RiskCase.event))
    
    if status:
        stmt = stmt.where(RiskCase.status == status)
    if priority:
        stmt = stmt.where(RiskCase.priority == priority)
        
    if search:
        # Simple search across ID or event subject
        from sqlalchemy import or_
        from packages.domain import Event
        stmt = stmt.join(RiskCase.event).where(
            or_(
                RiskCase.id.ilike(f"%{search}%"),
                Event.subject.ilike(f"%{search}%")
            )
        )
        
    if sort_by == "priority":
        # Hacky priority sort for SQLite (A > B string ordering isn't ideal but works for High/Med/Low)
        stmt = stmt.order_by(RiskCase.priority.desc() if sort_desc else RiskCase.priority.asc())
    elif sort_by == "sla":
        stmt = stmt.order_by(RiskCase.sla_deadline.desc() if sort_desc else RiskCase.sla_deadline.asc())
    else:
        stmt = stmt.order_by(RiskCase.created_at.desc() if sort_desc else RiskCase.created_at.asc())
        
    stmt = stmt.offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    cases = result.scalars().all()
    return cases

@router.get(
    "/{case_id}",
    response_model=dict,
    summary="Get Case Details",
    description="Retrieve full details of a specific risk case."
)
async def get_case(
    case_id: str, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    result = await db.execute(
        select(RiskCase)
        .where(RiskCase.id == case_id, RiskCase.organization_id == org_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    return {
        "id": case.id,
        "event_id": case.event_id,
        "status": case.status,
        "priority": case.priority,
        "attempt_count": case.attempt_count,
        "worker_id": case.worker_id,
        "claimed_at": case.claimed_at,
        "completed_at": case.completed_at,
        "created_at": case.created_at,
        "assigned_to": case.assigned_to
    }

@router.get(
    "/{case_id}/timeline",
    summary="Get Case Timeline",
    description="Retrieve the audit trail timeline for a specific case."
)
async def get_case_timeline(
    case_id: str, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # Verify ownership first
    case_res = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    if not case_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    result = await db.execute(
        select(AuditTrail)
        .where(AuditTrail.entity_type == "RiskCase", AuditTrail.entity_id == case_id)
        .order_by(AuditTrail.timestamp)
    )
    audits = result.scalars().all()
    
    timeline = []
    for audit in audits:
        timeline.append({
            "type": audit.action,
            "timestamp": audit.timestamp,
            "actor": audit.user_id or "system",
            "metadata": audit.metadata_json
        })
        
    return timeline

@router.get(
    "/{case_id}/evidence",
    summary="Get Case Evidence",
    description="Retrieve all evidence collected during the investigation of a case."
)
async def get_case_evidence(
    case_id: str, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # Verify ownership
    case_res = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    if not case_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    # First find investigation
    from packages.domain import Investigation
    inv_result = await db.execute(
        select(Investigation).where(Investigation.risk_case_id == case_id)
    )
    investigations = inv_result.scalars().all()
    
    if not investigations:
        return []
        
    # Get all evidence for all investigations of this case
    inv_ids = [inv.id for inv in investigations]
    ev_result = await db.execute(
        select(Evidence).where(Evidence.investigation_id.in_(inv_ids))
    )
    evidence_list = ev_result.scalars().all()
    
    return [
        {
            "id": ev.id,
            "type": ev.evidence_type,
            "value": ev.value,
            "severity": ev.severity,
            "confidence": ev.confidence,
            "explanation": ev.explanation,
            "created_at": ev.created_at
        }
        for ev in evidence_list
    ]

@router.get("/{case_id}/assessment")
async def get_case_assessment(
    case_id: str, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # Verify ownership
    case_res = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    if not case_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    result = await db.execute(
        select(RiskAssessment).where(RiskAssessment.risk_case_id == case_id)
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    return {
        "id": assessment.id,
        "risk_score": assessment.risk_score,
        "recommendation": assessment.recommendation,
        "rationale": assessment.rationale,
        "policy_id": assessment.policy_id,
        "policy_version": assessment.policy_version,
        "created_at": assessment.created_at
    }
@router.post("/{case_id}/assign")
async def assign_case(
    case_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    result = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case.assigned_to = user_id
    await db.commit()
    return {"status": "success", "assigned_to": user_id}

from packages.domain.notes import CaseNote
from packages.schemas.notes import CaseNoteCreate, CaseNoteResponse

@router.post("/{case_id}/notes", response_model=CaseNoteResponse)
async def create_note(
    case_id: str,
    note_data: CaseNoteCreate,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
    # user_id: str = Depends(get_authenticated_user)  # Ideally this
):
    import uuid
    from packages.domain import AuditTrail
    
    # 1. Verify ownership
    result = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # 2. Create note
    note = CaseNote(
        id=f"note_{uuid.uuid4().hex[:12]}",
        risk_case_id=case_id,
        author_id="Current User", # Mock user since auth isn't fully integrated here for the caller
        content=note_data.content
    )
    db.add(note)
    
    # 3. Create Audit
    audit = AuditTrail(
        id=f"audit_{uuid.uuid4().hex[:12]}",
        entity_type="RiskCase",
        entity_id=case_id,
        action="NOTE_ADDED",
        user_id="Current User",
        metadata_json={"note_id": note.id}
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(note)
    return note

@router.get("/{case_id}/notes", response_model=List[CaseNoteResponse])
async def list_notes(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # 1. Verify ownership
    result = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # 2. Fetch notes
    result = await db.execute(
        select(CaseNote).where(CaseNote.risk_case_id == case_id).order_by(CaseNote.created_at.asc())
    )
    return result.scalars().all()

@router.post("/{case_id}/start_review")
async def start_review(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    """Record that an analyst has opened the case to begin manual review."""
    from datetime import datetime
    
    result = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if not case.analyst_review_started_at:
        case.analyst_review_started_at = datetime.utcnow()
        await db.commit()
        
    return {"status": "success", "analyst_review_started_at": case.analyst_review_started_at}

@router.get("/validation/report")
async def get_validation_report(
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    from packages.domain.validation import ReplayRun, ValidationResult, ReplayEvent
    from sqlalchemy import desc
    
    # Get latest run for the org
    run_res = await db.execute(
        select(ReplayRun)
        .where(ReplayRun.organization_id == org_id)
        .order_by(desc(ReplayRun.created_at))
        .limit(1)
    )
    latest_run = run_res.scalar_one_or_none()
    
    if not latest_run:
        return {"total_replayed": 0}
        
    res_query = await db.execute(select(ValidationResult).where(ValidationResult.run_id == latest_run.id))
    results = res_query.scalars().all()
@router.get(
    "/{case_id}/evidence",
    summary="Get Case Evidence",
    description="Retrieve all evidence collected during the investigation of a case."
)
async def get_case_evidence(
    case_id: str, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # Verify ownership
    case_res = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    if not case_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    # First find investigation
    from packages.domain import Investigation
    inv_result = await db.execute(
        select(Investigation).where(Investigation.risk_case_id == case_id)
    )
    investigations = inv_result.scalars().all()
    
    if not investigations:
        return []
        
    # Get all evidence for all investigations of this case
    inv_ids = [inv.id for inv in investigations]
    ev_result = await db.execute(
        select(Evidence).where(Evidence.investigation_id.in_(inv_ids))
    )
    evidence_list = ev_result.scalars().all()
    
    return [
        {
            "id": ev.id,
            "type": ev.evidence_type,
            "value": ev.value,
            "severity": ev.severity,
            "confidence": ev.confidence,
            "explanation": ev.explanation,
            "created_at": ev.created_at
        }
        for ev in evidence_list
    ]

@router.get("/{case_id}/assessment")
async def get_case_assessment(
    case_id: str, 
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # Verify ownership
    case_res = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    if not case_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Case not found")

    result = await db.execute(
        select(RiskAssessment).where(RiskAssessment.risk_case_id == case_id)
    )
    assessment = result.scalar_one_or_none()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    return {
        "id": assessment.id,
        "risk_score": assessment.risk_score,
        "recommendation": assessment.recommendation,
        "rationale": assessment.rationale,
        "policy_id": assessment.policy_id,
        "policy_version": assessment.policy_version,
        "created_at": assessment.created_at
    }
@router.post("/{case_id}/assign")
async def assign_case(
    case_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    result = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case.assigned_to = user_id
    await db.commit()
    return {"status": "success", "assigned_to": user_id}

from packages.domain.notes import CaseNote
from packages.schemas.notes import CaseNoteCreate, CaseNoteResponse

@router.post("/{case_id}/notes", response_model=CaseNoteResponse)
async def create_note(
    case_id: str,
    note_data: CaseNoteCreate,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
    # user_id: str = Depends(get_authenticated_user)  # Ideally this
):
    import uuid
    from packages.domain import AuditTrail
    
    # 1. Verify ownership
    result = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # 2. Create note
    note = CaseNote(
        id=f"note_{uuid.uuid4().hex[:12]}",
        risk_case_id=case_id,
        author_id="Current User", # Mock user since auth isn't fully integrated here for the caller
        content=note_data.content
    )
    db.add(note)
    
    # 3. Create Audit
    audit = AuditTrail(
        id=f"audit_{uuid.uuid4().hex[:12]}",
        entity_type="RiskCase",
        entity_id=case_id,
        action="NOTE_ADDED",
        user_id="Current User",
        metadata_json={"note_id": note.id}
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(note)
    return note

@router.get("/{case_id}/notes", response_model=List[CaseNoteResponse])
async def list_notes(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    # 1. Verify ownership
    result = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # 2. Fetch notes
    result = await db.execute(
        select(CaseNote).where(CaseNote.risk_case_id == case_id).order_by(CaseNote.created_at.asc())
    )
    return result.scalars().all()

@router.post("/{case_id}/start_review")
async def start_review(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    """Record that an analyst has opened the case to begin manual review."""
    from datetime import datetime
    
    result = await db.execute(select(RiskCase).where(RiskCase.id == case_id, RiskCase.organization_id == org_id))
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if not case.analyst_review_started_at:
        case.analyst_review_started_at = datetime.utcnow()
        await db.commit()
        
    return {"status": "success", "analyst_review_started_at": case.analyst_review_started_at}

@router.get("/validation/report")
async def get_validation_report(
    db: AsyncSession = Depends(get_db),
    org_id: str = Depends(get_current_organization)
):
    from packages.domain.validation import ReplayRun, ValidationResult, ReplayEvent
    from sqlalchemy import desc
    
    # Get latest run for the org
    run_res = await db.execute(
        select(ReplayRun)
        .where(ReplayRun.organization_id == org_id)
        .order_by(desc(ReplayRun.created_at))
        .limit(1)
    )
    latest_run = run_res.scalar_one_or_none()
    
    if not latest_run:
        return {"total_replayed": 0}
        
    res_query = await db.execute(select(ValidationResult).where(ValidationResult.run_id == latest_run.id))
    results = res_query.scalars().all()
    
    total_cases = len(results)
    if total_cases == 0:
        return {"total_replayed": 0}
        
    # Aggregate Metrics
    total_manual_inv_sec = 0
    total_manual_analyst_sec = 0
    total_rp_inv_sec = 0
    total_rp_analyst_sec = 0
    
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    decision_matches = 0
    
    for r in results:
        ev_res = await db.execute(select(ReplayEvent).where(ReplayEvent.id == r.event_id))
        ev = ev_res.scalar_one()
        
        total_manual_inv_sec += ev.manual_investigation_time_sec or 0
        total_manual_analyst_sec += ev.manual_analyst_time_sec or 0
        total_rp_inv_sec += r.riskpilot_investigation_time_sec or 0
        total_rp_analyst_sec += r.riskpilot_analyst_time_sec or 0
        
        if r.decision_match:
            decision_matches += 1
            
        md = (ev.manual_decision or "").upper()
        rd = (r.riskpilot_recommendation or "").upper()
        
        is_rp_fraud = rd in ["ESCALATE", "HOLD"]
        is_manual_fraud = md in ["ESCALATE", "HOLD"]
        
        if is_rp_fraud and is_manual_fraud:
            tp += 1
        elif is_rp_fraud and not is_manual_fraud:
            fp += 1
        elif not is_rp_fraud and not is_manual_fraud:
            tn += 1
        elif not is_rp_fraud and is_manual_fraud:
            fn += 1
            
    total_manual_sec = total_manual_inv_sec + total_manual_analyst_sec
    total_rp_sec = total_rp_inv_sec + total_rp_analyst_sec
    time_saved_sec = total_manual_sec - total_rp_sec
    
    precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 100.0
    recall = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 100.0
    
    # Assume $150 cost per False Positive (lifetime value churn / manual support cost)
    fp_cost = fp * 150
    
    return {
        "total_replayed": total_cases,
        "metrics": {
            "time_saved_pct": round((time_saved_sec / total_manual_sec * 100) if total_manual_sec > 0 else 0, 1),
            "time_saved_min_per_case": round((time_saved_sec / 60) / total_cases, 1),
            "manual_baseline_avg_min": round((total_manual_sec / 60) / total_cases, 1),
            "riskpilot_inv_avg_min": round((total_rp_inv_sec / 60) / total_cases, 1),
            "analyst_review_avg_min": round((total_rp_analyst_sec / 60) / total_cases, 1),
            "false_positive_rate_pct": round((fp / total_cases) * 100, 1),
            "decision_overturn_rate_pct": round(((total_cases - decision_matches) / total_cases) * 100, 1),
            "precision_pct": round(precision, 1),
            "recall_pct": round(recall, 1),
            "false_positive_cost_usd": fp_cost
        }
    }
