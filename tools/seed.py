import asyncio
import sys
import os
import uuid

# Add root project dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.api.app.database import engine, async_session
from packages.domain import Base, Organization, ApiKey, Policy, WebhookEndpoint

async def seed():
    # 1. Create DB Schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as db:
        # 2. Create Organization
        org_id = f"org_{uuid.uuid4().hex[:8]}"
        org = Organization(id=org_id, name="Demo Fintech Inc.")
        db.add(org)
        
        # 3. Create API Key
        raw_key = f"api_{org_id}_{uuid.uuid4().hex[:8]}"
        # We store the raw key in a file so run-evaluation.ps1 can use it
        with open(".demo_env", "w") as f:
            f.write(f"DEMO_API_KEY={raw_key}\n")
            f.write(f"DEMO_ORG_ID={org_id}\n")
            
        import hashlib
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = ApiKey(id=f"key_{uuid.uuid4().hex[:8]}", organization_id=org_id, key_hash=key_hash, name="Demo Key")
        db.add(api_key)
        
        # 4. Create default policy
        policy = Policy(
            id=f"pol_{uuid.uuid4().hex[:8]}",
            organization_id=org_id,
            name="Default Risk Policy",
            version="1.0",
            rules_config={"risk_weights": {"vpn_usage": 10, "upi_abuse_ring": 25}},
            is_active=True
        )
        db.add(policy)
        
        # 5. Create a Webhook Endpoint (optional, points to a local test receiver)
        ep = WebhookEndpoint(
            id=f"we_{uuid.uuid4().hex[:8]}",
            organization_id=org_id,
            url="http://127.0.0.1:8081/webhook/test",
            secret="demo_secret",
            is_active=True
        )
        db.add(ep)
        
        await db.commit()
        print(f"Seed complete! Org ID: {org_id}")

if __name__ == "__main__":
    asyncio.run(seed())
