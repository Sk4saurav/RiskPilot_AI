import hashlib
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid
from apps.api.app.models import AuditReport

class AuditGenerator:
    """
    Generates tamper-evident, append-only audit logs using SHA-256 hash linking.
    """

    @staticmethod
    def hash_payload(previous_hash: str, payload: dict) -> str:
        """
        Creates a deterministic SHA-256 hash from the previous hash and the current payload.
        """
        payload_str = json.dumps(payload, sort_keys=True)
        combined_string = f"{previous_hash}{payload_str}"
        return hashlib.sha256(combined_string.encode('utf-8')).hexdigest()

    @classmethod
    async def get_latest_hash(cls, db: AsyncSession) -> str:
        """
        Retrieves the hash of the most recent audit report in the chain.
        Returns a genesis string if the chain is empty.
        """
        result = await db.execute(
            select(AuditReport).order_by(desc(AuditReport.decision_timestamp)).limit(1)
        )
        latest_report = result.scalars().first()
        
        if latest_report and latest_report.hash:
            return latest_report.hash
        return "GENESIS_HASH_000000000000000000000000000000"

    @classmethod
    async def create_audit_record(
        cls, 
        db: AsyncSession, 
        risk_event_id: str, 
        human_decision: str, 
        full_report_json: dict
    ) -> AuditReport:
        """
        Creates a new hash-linked audit record.
        """
        previous_hash = await cls.get_latest_hash(db)
        
        # Calculate the new hash including all critical DB columns
        payload_to_hash = {
            "risk_event_id": risk_event_id,
            "human_decision": human_decision,
            "full_report_json": full_report_json
        }
        new_hash = cls.hash_payload(previous_hash, payload_to_hash)

        audit_report = AuditReport(
            id=str(uuid.uuid4()),
            risk_event_id=risk_event_id,
            previous_hash=previous_hash,
            hash=new_hash,
            full_report_json=full_report_json,
            human_decision=human_decision,
            decision_timestamp=datetime.utcnow()
        )
        
        db.add(audit_report)
        await db.commit()
        await db.refresh(audit_report)
        
        return audit_report

    @classmethod
    async def verify_chain_integrity(cls, db: AsyncSession) -> bool:
        """
        Verifies the cryptographic integrity of the entire audit chain.
        Returns True if the chain is intact, False if tampered.
        """
        result = await db.execute(
            select(AuditReport).order_by(AuditReport.decision_timestamp)
        )
        reports = result.scalars().all()
        
        if not reports:
            return True # Empty chain is valid
            
        current_hash = "GENESIS_HASH_000000000000000000000000000000"
        
        for report in reports:
            if report.previous_hash != current_hash:
                return False # Link broken
            
            payload_to_hash = {
                "risk_event_id": report.risk_event_id,
                "human_decision": report.human_decision,
                "full_report_json": report.full_report_json
            }
            calculated_hash = cls.hash_payload(report.previous_hash, payload_to_hash)
            if calculated_hash != report.hash:
                return False # Payload modified
                
            current_hash = report.hash
            
        return True
