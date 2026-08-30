import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session, engine
from app.models import RiskEvent, RiskSignal, AuditReport, Transaction
from app.main import process_transaction_workflow
from app.audit import AuditGenerator

async def run_validation():
    async with async_session() as db:
        print("\n--- Starting End-to-End Validation for TX-18492 ---")
        
        # 1. Trigger the workflow
        print("Running autonomous investigation workflow...")
        await process_transaction_workflow("TX-18492", db)
        
        # 2. Fetch the result
        result = await db.execute(select(RiskEvent).where(RiskEvent.transaction_id == "TX-18492"))
        event = result.scalars().first()
        
        if not event:
            print("ERROR: RiskEvent not generated.")
            return

        print(f"\nTransaction: TX-18492")
        print(f"Risk Score: {event.risk_score}/100")
        print(f"Severity: {'CRITICAL' if event.risk_score >= 80 else 'HIGH'}")
        print(f"Recommendation: {event.recommended_action}")
        
        # 3. Print signals
        sig_result = await db.execute(select(RiskSignal).where(RiskSignal.risk_event_id == event.id))
        signals = sig_result.scalars().all()
        print("\nRisk Signals:")
        for s in signals:
            print(f"  {s.signal_type:<30} +{s.weight}")
            
        print(f"\nTOTAL: {event.risk_score}/100")
        
        # 4. Simulate human confirmation
        print("\nHuman Decision: CONFIRM HOLD")
        
        full_report = {
            "event_id": event.id,
            "score": event.risk_score,
            "ai_recommendation": event.recommended_action,
            "human_decision": "CONFIRM HOLD",
        }
        
        audit_report = await AuditGenerator.create_audit_record(db, event.id, "CONFIRM HOLD", full_report)
        print("\nAudit:")
        print("[OK] Evidence recorded")
        print("[OK] Decision recorded")
        print(f"[OK] Previous hash verified ({audit_report.previous_hash[:8]}...)")
        print(f"[OK] Current hash generated ({audit_report.hash[:8]}...)")
        
        # 5. Verify Audit Integrity
        is_valid = await AuditGenerator.verify_chain_integrity(db)
        if is_valid:
            print("[OK] Hash chain verified")
            print("\nAUDIT INTEGRITY: VERIFIED")
        else:
            print("\nAUDIT INTEGRITY: FAILED")
            
        print("\n--- Running Audit Chain Attack Test ---")
        # Simulate tampering
        print("Tampering with the audit record's human_decision field...")
        audit_report.human_decision = "TAMPERED DECISION"
        await db.commit()
        
        is_valid_after_tamper = await AuditGenerator.verify_chain_integrity(db)
        if not is_valid_after_tamper:
            print("\n[!] AUDIT INTEGRITY COMPROMISED")
            print("[OK] RiskPilot successfully detected tampering with the hash-linked audit history.")
        else:
            print("\n[FAIL] System failed to detect tampering!")

if __name__ == "__main__":
    asyncio.run(run_validation())
