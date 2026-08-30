import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from .claim import claim_new_case, recover_stale_claims
from .service import InvestigationService

logger = logging.getLogger(__name__)

class InvestigationRunner:
    def __init__(self, session_maker, worker_id: str, poll_interval: int = 5, stale_timeout: int = 10):
        self.session_maker = session_maker
        self.worker_id = worker_id
        self.poll_interval = poll_interval
        self.stale_timeout = stale_timeout
        self.service = InvestigationService()
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info(f"Worker {self.worker_id} started. Polling every {self.poll_interval}s.")
        
        while self.is_running:
            try:
                await self._run_loop_cycle()
            except Exception as e:
                logger.error(f"Worker encountered unexpected error: {e}")
            
            await asyncio.sleep(self.poll_interval)
            
    async def stop(self):
        self.is_running = False
        logger.info(f"Worker {self.worker_id} stopping...")

    async def _run_loop_cycle(self):
        # 1. Recover stale claims
        async with self.session_maker() as session:
            recovered = await recover_stale_claims(session, self.stale_timeout)
            if recovered > 0:
                logger.info(f"Worker {self.worker_id} recovered {recovered} stale claims.")
                
        # 2. Claim a new case
        case_id = None
        async with self.session_maker() as session:
            case_id = await claim_new_case(session, self.worker_id)
            
        if not case_id:
            return # No new cases
            
        logger.info(f"Worker {self.worker_id} claimed case {case_id}. Starting investigation.")
        
        # 3. Investigate the case
        async with self.session_maker() as session:
            try:
                success = await self.service.investigate_case(session, case_id, self.worker_id)
                if success:
                    logger.info(f"Worker {self.worker_id} completed investigation for case {case_id}.")
                else:
                    logger.warning(f"Worker {self.worker_id} failed to investigate case {case_id} (not found).")
            except Exception as e:
                logger.error(f"Error during investigation of case {case_id}: {e}")
                await session.rollback()
                await self._handle_investigation_failure(case_id, str(e))
                
    async def _handle_investigation_failure(self, case_id: str, error_msg: str):
        from packages.domain import RiskCase
        from sqlalchemy import update
        
        # Attempt to mark the case as failed/retried
        try:
            async with self.session_maker() as session:
                from sqlalchemy import select
                case = (await session.execute(select(RiskCase).where(RiskCase.id == case_id))).scalar_one_or_none()
                if case:
                    case.last_error = error_msg
                    if case.attempt_count >= 3:
                        case.status = "MANUAL_REVIEW_REQUIRED"
                        logger.error(f"Case {case_id} exceeded max retries. Manual review required.")
                    else:
                        case.status = "NEW" # Return to queue
                    await session.commit()
        except Exception as e:
            logger.critical(f"Failed to record investigation failure for case {case_id}: {e}")
