import asyncio
from collections import defaultdict
from fastapi import APIRouter, Request, Response, HTTPException

router = APIRouter(
    prefix="/v1/simulator",
    tags=["Simulator"],
)

flakey_counter = defaultdict(int)

@router.post("/webhook-receiver")
async def webhook_receiver(request: Request, mode: str = "200"):
    """
    Development-only Webhook Receiver Simulator.
    Controls via ?mode query parameter:
    - '200': Success
    - '500': Internal Server Error
    - 'timeout': Simulate slow response (sleeps for 10 seconds)
    - 'invalid': Return non-JSON invalid response
    - 'flakey': Returns 500 twice, then 200 on the third attempt for the same event
    - 'secure': Verifies the HMAC-SHA256 signature using the provided ?secret query param
    """
    
    if mode == "secure":
        secret = request.query_params.get("secret")
        if not secret:
            return Response(content="Missing secret query param", status_code=400)
            
        timestamp = request.headers.get("X-RiskPilot-Timestamp")
        signature = request.headers.get("X-RiskPilot-Signature")
        
        if not timestamp or not signature:
            return Response(content="Missing signature headers", status_code=401)
            
        raw_body = await request.body()
        signed_payload = f"{timestamp}." + raw_body.decode('utf-8')
        
        import hmac, hashlib
        expected_sig = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_sig, signature):
            return Response(content="Invalid Signature", status_code=401)
            
        return {"status": "verified"}
        
    elif mode == "200":
        return {"status": "received"}
        
    elif mode == "flakey":
        event_id = request.headers.get("X-RiskPilot-Event-ID", "unknown")
        flakey_counter[event_id] += 1
        if flakey_counter[event_id] <= 2:
            return Response(content="Flakey Error Simulator", status_code=500)
        return {"status": "received on retry"}
        
    elif mode == "500":
        return Response(content="Internal Server Error Simulator", status_code=500)
        
    elif mode == "timeout":
        await asyncio.sleep(10.0) # Will trigger the 5.0s timeout in our dispatcher
        return {"status": "late"}
        
    elif mode == "invalid":
        return Response(content="<!DOCTYPE html><html><body>Invalid</body></html>", status_code=200, media_type="text/html")
        
    else:
        return {"status": "received"}
