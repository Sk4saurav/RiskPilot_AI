import asyncio
import json
import uuid
from datetime import datetime, timedelta
import random

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, async_session, engine
from app.models import Base

async def generate_synthetic_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        # Clear existing data for a clean slate
        from app.models import AuditReport, RiskSignal, EntityRelationship, RiskEvent, Transaction, Customer
        for model in [AuditReport, RiskSignal, EntityRelationship, RiskEvent, Transaction, Customer]:
            await db.execute(model.__table__.delete())
        
        # Create Customers
        customers = [
            Customer(id=str(uuid.uuid4()), name="Alice Smith", account_age_days=1200, risk_profile="LOW"),
            Customer(id=str(uuid.uuid4()), name="Bob Jones", account_age_days=45, risk_profile="MEDIUM"),
            Customer(id="ade6b26e-b6d0-460a-aa95-674626b2310f", name="Charlie Brown", account_age_days=2, risk_profile="HIGH")
        ]
        db.add_all(customers)
        
        # Insert normal transactions ONLY so TX-18492 can be ingested live
        tx1 = Transaction(
            id="TX-10001",
            customer_id=customers[0].id,
            amount=45.00,
            currency="USD",
            location="New York, USA",
            ip_address="192.168.1.100",
            device_id="dev_iphone_12_alice",
            beneficiary_id="merchant_coffee_shop",
            status="PENDING"
        )
        
        tx2 = Transaction(
            id="TX-10002",
            customer_id=customers[1].id,
            amount=1500.00,
            currency="USD",
            location="Chicago, USA",
            ip_address="192.168.1.200",
            device_id="dev_macbook_bob",
            beneficiary_id="merchant_electronics",
            status="PENDING"
        )

        db.add_all([tx1, tx2])
        await db.commit()
        print("Synthetic data generated successfully.")

if __name__ == "__main__":
    asyncio.run(generate_synthetic_data())
