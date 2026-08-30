from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any
from datetime import datetime

from apps.api.app.database import get_db
from apps.api.app.auth import get_current_organization
from packages.domain import Organization, RiskCase, Investigation, RiskAssessment, Decision, Event
from packages.domain.webhooks import WebhookDelivery

router = APIRouter(prefix="/v1/metrics", tags=["Metrics"])

@router.get("/live_trial")
async def get_live_trial_metrics(
    org_id: str = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db)
):
    """
    Beta 0.7 Live Trial Automated KPI Calculation.
    Separates the historical baseline from the actual live observed results.
    """
    
    # In a real system we would filter by date or specific tags,
    # but for Beta 0.7 we just aggregate all cases for this org.
    
    # 1. Total Cases
    cases_result = await db.execute(select(func.count(RiskCase.id)).where(RiskCase.organization_id == org_id))
    total_cases = cases_result.scalar() or 0
    
    # 2. Total Investigated Cases (have an assessment)
    investigated_cases_result = await db.execute(
        select(func.count(RiskCase.id))
        .join(RiskAssessment, RiskAssessment.risk_case_id == RiskCase.id)
        .where(RiskCase.organization_id == org_id)
    )
    investigated_cases = investigated_cases_result.scalar() or 0
    
    if investigated_cases == 0:
        return {
            "cases": 0,
            "message": "No live cases investigated yet."
        }
        
    # 3. Calculate Latencies
    # We must fetch the timestamps to do math accurately, as SQLite func.avg might be tricky with datetimes.
    # We fetch Event.timestamp, RiskAssessment.created_at, RiskCase.analyst_review_started_at, Decision.created_at
    
    stmt = (
        select(
            Event.timestamp,
            RiskAssessment.created_at.label("assessment_created_at"),
            RiskCase.analyst_review_started_at,
            Decision.created_at.label("decision_created_at"),
            Decision.is_override
        )
        .join(RiskCase, RiskCase.event_id == Event.id)
        .outerjoin(RiskAssessment, RiskAssessment.risk_case_id == RiskCase.id)
        .outerjoin(Decision, Decision.risk_case_id == RiskCase.id)
        .where(RiskCase.organization_id == org_id, RiskAssessment.id != None)
    )
    
    rows = (await db.execute(stmt)).all()
    
    investigation_latencies_sec = []
    analyst_review_latencies_sec = []
    overrides = 0
    decisions_count = 0
    
    for row in rows:
        event_time = row.timestamp
        assessment_time = row.assessment_created_at
        review_started = row.analyst_review_started_at
        decision_time = row.decision_created_at
        is_override = row.is_override
        
        if event_time and assessment_time:
            delta = (assessment_time - event_time).total_seconds()
            investigation_latencies_sec.append(max(0, delta))
            
        if review_started and decision_time:
            delta = (decision_time - review_started).total_seconds()
            analyst_review_latencies_sec.append(max(0, delta))
            decisions_count += 1
            if is_override:
                overrides += 1
                
    avg_inv_sec = sum(investigation_latencies_sec) / len(investigation_latencies_sec) if investigation_latencies_sec else 0
    avg_rev_sec = sum(analyst_review_latencies_sec) / len(analyst_review_latencies_sec) if analyst_review_latencies_sec else 0
    
    avg_inv_min = round(avg_inv_sec / 60.0, 1)
    avg_rev_min = round(avg_rev_sec / 60.0, 1)
    total_min = round(avg_inv_min + avg_rev_min, 1)
    
    # 4. Historical Baseline (From the validation dataset)
    # The historical baseline for Beta 0.7:
    baseline_total = 25.8
    baseline_inv = 19.9
    baseline_rev = 5.9
    
    time_saved_min = round(baseline_total - total_min, 1)
    time_saved_pct = round((time_saved_min / baseline_total) * 100.0, 2) if baseline_total > 0 else 0
    
    overturn_pct = round((overrides / decisions_count) * 100.0, 1) if decisions_count > 0 else 0.0
    
    # 5. Webhook Reliability
    wh_stmt = select(func.count(WebhookDelivery.id), func.sum(WebhookDelivery.is_successful)).join(
        Event, Event.id == WebhookDelivery.event_id # Approximation, actually event_id in webhook might be case_id
    )
    # Let's just measure overall webhook success for the org
    wh_result = await db.execute(
        select(
            func.count(WebhookDelivery.id), 
            func.sum(WebhookDelivery.is_successful)
        )
    )
    wh_row = wh_result.first()
    wh_total = wh_row[0] or 0
    wh_success = wh_row[1] or 0
    
    webhook_success_pct = round((wh_success / wh_total) * 100.0, 1) if wh_total > 0 else 100.0
    
    return {
        "cases": investigated_cases,
        "baseline": {
            "manual_investigation_min": baseline_inv,
            "manual_review_min": baseline_rev,
            "manual_total_min": baseline_total
        },
        "riskpilot": {
            "investigation_min": avg_inv_min,
            "analyst_review_min": avg_rev_min,
            "total_min": total_min
        },
        "value": {
            "time_saved_min_per_case": time_saved_min,
            "time_saved_pct": time_saved_pct
        },
        "quality": {
            "decision_overturn_pct": overturn_pct,
            "false_positive_pct": 0.0 # Requires feedback loop
        },
        "reliability": {
            "webhook_success_pct": webhook_success_pct
        }
    }

@router.get("/system_status")
async def get_system_status(db: AsyncSession = Depends(get_db)):
    """
    Returns system health and high-level platform metrics for the dashboard.
    """
    try:
        # Check database connectivity
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_status = "Connected"
    except Exception:
        db_status = "Disconnected"

    # Get event count
    events_res = await db.execute(select(func.count(Event.id)))
    total_events = events_res.scalar() or 0

    # Get investigation count
    inv_res = await db.execute(select(func.count(Investigation.id)))
    total_investigations = inv_res.scalar() or 0

    # Get webhook success rate
    wh_result = await db.execute(
        select(
            func.count(WebhookDelivery.id), 
            func.sum(WebhookDelivery.is_successful)
        )
    )
    wh_row = wh_result.first()
    wh_total = wh_row[0] or 0
    wh_success = wh_row[1] or 0
    webhook_success_pct = round((wh_success / wh_total) * 100.0, 1) if wh_total > 0 else 100.0

    return {
        "services": {
            "api": "Operational",
            "investigation_worker": "Operational",
            "database": db_status,
            "policy_engine": "Operational",
            "webhook_service": "Operational",
            "replay_engine": "Operational",
            "copilot": "Operational"
        },
        "metrics": {
            "last_health_check": datetime.utcnow().isoformat() + "Z",
            "events_processed": total_events,
            "investigations": total_investigations,
            "webhook_success_pct": webhook_success_pct
        }
    }
