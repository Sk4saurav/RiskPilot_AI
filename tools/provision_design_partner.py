import asyncio
import uuid
import secrets
from datetime import datetime
import sys

# Ensure apps/api is in the path
sys.path.append("apps/api")

from app.database import async_session, engine
from packages.domain import Organization, Policy
from app.routers.orgs import hash_api_key
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def provision():
    async with async_session() as session:
        # Create Design Partner Org
        org_id = "org_dp_" + uuid.uuid4().hex[:8]
        org = Organization(id=org_id, name="Design Partner Alpha")
        session.add(org)
        
        # Create API Key
        raw_secret = secrets.token_urlsafe(32)
        prefix = f"rp_live_{raw_secret[:4]}"
        full_key = f"rp_live_{raw_secret}"
        key_hash = hash_api_key(full_key)
        
        # Insert raw API key (using raw SQL because ApiKey isn't in packages.domain.validation, 
        # it's usually defined in apps/api/app/models.py which we might not have imported)
        key_id = f"key_{uuid.uuid4().hex[:12]}"
        await session.execute(
            text("INSERT INTO api_keys (id, organization_id, name, key_hash, prefix, created_at) "
                 "VALUES (:id, :org_id, :name, :key_hash, :prefix, :created_at)"),
            {"id": key_id, "org_id": org_id, "name": "Production Events Key", "key_hash": key_hash, "prefix": prefix, "created_at": datetime.utcnow()}
        )
        
        # Create Webhook Endpoint
        webhook_id = f"wh_{uuid.uuid4().hex[:12]}"
        webhook_secret = f"whsec_{secrets.token_hex(16)}"
        await session.execute(
            text("INSERT INTO webhook_endpoints (id, organization_id, url, secret, created_at) "
                 "VALUES (:id, :org_id, :url, :secret, :created_at)"),
            {"id": webhook_id, "org_id": org_id, "url": "https://api.designpartner.com/webhooks/riskpilot", "secret": webhook_secret, "created_at": datetime.utcnow()}
        )
        
        # Create the dynamic policy we validated in Beta 0.7 Phase 3
        rules = {
            "threshold": 50, 
            "positive_history_tiers": {"1": -5, "2-4": -10, "5+": -15},
            "customer_support_verification": -30,
            "vip_status": -30,
            "upi_abuse_ring": 25
        }
        thresholds = {
            "rules": [
                {
                    "when": {"field": "amount_cents", "operator": ">=", "value": 500000},
                    "severity_ranges": {"LOW": [0, 20], "MEDIUM": [21, 40], "HIGH": [41, 79], "CRITICAL": [80, 100]}
                },
                {
                    "when": {"default": True},
                    "severity_ranges": {"LOW": [0, 49], "MEDIUM": [50, 79], "HIGH": [80, 89], "CRITICAL": [90, 100]}
                }
            ]
        }
        policy_id = f"pol_{uuid.uuid4().hex[:12]}"
        pol = Policy(id=policy_id, organization_id=org_id, name="Design Partner Default Policy", is_active=True, rules_config=rules, thresholds=thresholds, version=1)
        session.add(pol)
        
        await session.commit()
        
        print("Design Partner Provisioned Successfully")
        print("="*40)
        print(f"Organization ID:   {org_id}")
        print(f"Policy ID:         {policy_id}")
        print(f"Webhook ID:        {webhook_id}")
        print(f"Webhook URL:       https://api.designpartner.com/webhooks/riskpilot")
        print(f"Webhook Secret:    {webhook_secret}")
        print("="*40)
        print("CRITICAL: Share this API key securely. It will not be shown again.")
        print(f"API Key:           {full_key}")
        print("="*40)

if __name__ == "__main__":
    asyncio.run(provision())
