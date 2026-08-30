import asyncio
import logging
import uuid
import sys
import os

# Add root project dir to path so we can import packages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from apps.api.app.database import async_session
from workers.investigation.runner import InvestigationRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

async def main():
    worker_id = f"worker_{uuid.uuid4().hex[:8]}"
    
    runner = InvestigationRunner(
        session_maker=async_session,
        worker_id=worker_id,
        poll_interval=5,
        stale_timeout=10
    )
    
    try:
        await runner.start()
    except KeyboardInterrupt:
        await runner.stop()

if __name__ == "__main__":
    asyncio.run(main())
