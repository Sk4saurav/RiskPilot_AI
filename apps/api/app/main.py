from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from sqlalchemy.ext.asyncio import AsyncSession
from apps.api.app.database import engine, get_db
from packages.domain.base import Base

from contextlib import asynccontextmanager

# Add root project dir to path so we can import packages
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from apps.api.app.routers import ingest, cases, policies, decisions, copilot, orgs, auth, realtime, webhooks, validation

import asyncio
import httpx
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from apps.api.app.database import async_session
from packages.domain.webhooks import WebhookDelivery, WebhookEndpoint
from sqlalchemy import select

async def webhook_retry_worker():
    while True:
        try:
            async with async_session() as session:
                # Find pending retries
                stmt = select(WebhookDelivery).join(WebhookEndpoint).where(
                    WebhookDelivery.is_successful == False,
                    WebhookDelivery.next_retry_at != None,
                    WebhookDelivery.next_retry_at <= datetime.utcnow(),
                    WebhookDelivery.attempt_count < 5,
                    WebhookEndpoint.is_active == True
                )
                deliveries = (await session.execute(stmt)).scalars().all()
                
                if deliveries:
                    async with httpx.AsyncClient() as client:
                        for delivery in deliveries:
                            # Re-fetch endpoint explicitly if needed, but it's joined
                            endpoint = await session.get(WebhookEndpoint, delivery.endpoint_id)
                            if not endpoint:
                                continue
                                
                            payload_str = json.dumps(delivery.payload, separators=(',', ':'))
                            signature = hmac.new(
                                endpoint.secret.encode('utf-8'),
                                payload_str.encode('utf-8'),
                                hashlib.sha256
                            ).hexdigest()
                            
                            delivery.attempt_count += 1
                            
                            try:
                                response = await client.post(
                                    endpoint.url, 
                                    content=payload_str,
                                    headers={
                                        "Content-Type": "application/json",
                                        "X-RiskPilot-Event": delivery.event_type,
                                        "X-RiskPilot-Signature": signature
                                    },
                                    timeout=5.0
                                )
                                delivery.status_code = str(response.status_code)
                                delivery.is_successful = 200 <= response.status_code < 300
                                if delivery.is_successful:
                                    delivery.delivered_at = datetime.utcnow()
                                    delivery.next_retry_at = None
                                else:
                                    delivery.last_error = response.text
                                    delivery.next_retry_at = datetime.utcnow() + timedelta(minutes=delivery.attempt_count * 2)
                            except Exception as e:
                                delivery.status_code = "ERROR"
                                delivery.is_successful = False
                                delivery.last_error = str(e)
                                delivery.next_retry_at = datetime.utcnow() + timedelta(minutes=delivery.attempt_count * 2)
                                
                    await session.commit()
        except Exception as e:
            print(f"Webhook retry worker error: {e}")
            
        await asyncio.sleep(10) # Poll every 10 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting API...")
    # Initialize DB schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Start Webhook Retry background task
    retry_task = asyncio.create_task(webhook_retry_worker())
    
    yield
    print("Shutting down API...")
    retry_task.cancel()
    await engine.dispose()

app = FastAPI(
    title="RiskPilot API",
    version="0.3.0",
    lifespan=lifespan
)

# Allow all origins for Alpha
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(orgs.router)
app.include_router(ingest.router)
app.include_router(cases.router)
app.include_router(policies.router)
app.include_router(decisions.router)
app.include_router(validation.router)
app.include_router(copilot.router)
app.include_router(realtime.router)
app.include_router(webhooks.router)
from apps.api.app.routers import metrics
app.include_router(metrics.router)

import uuid
from fastapi import Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.detail if isinstance(exc.detail, str) and exc.detail.isupper() else "API_ERROR",
                "message": exc.detail
            }
        }
    )

@app.get("/metrics")
def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import text
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/")
async def root():
    return {"message": "RiskPilot Platform API Online"}
