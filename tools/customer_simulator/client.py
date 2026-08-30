import httpx
import asyncio

class RiskPilotClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    async def send_event(self, event: dict, client: httpx.AsyncClient):
        try:
            response = await client.post(
                f"{self.base_url}/v1/events/ingest",
                json=event,
                headers=self.headers,
                timeout=10.0
            )
            return response.status_code, response.json() if response.status_code < 400 else response.text
        except Exception as e:
            return 500, str(e)
            
    async def send_batch(self, events: list, duplicate_count: int = 0):
        # Add intentional duplicates for idempotency testing
        if duplicate_count > 0 and len(events) > 0:
            import random
            dupes = random.choices(events, k=duplicate_count)
            events.extend(dupes)
            # Shuffle them so duplicates happen naturally
            random.shuffle(events)
            
        print(f"Sending {len(events)} events ({len(events)-duplicate_count} unique, {duplicate_count} duplicates)...")
        
        results = {"success": 0, "failed": 0}
        
        # Limit concurrency to not overwhelm the local dev server
        semaphore = asyncio.Semaphore(50)
        
        async def bounded_send(evt, client):
            async with semaphore:
                status, res = await self.send_event(evt, client)
                if status < 400:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    
        async with httpx.AsyncClient() as client:
            tasks = [bounded_send(evt, client) for evt in events]
            await asyncio.gather(*tasks)
            
        print(f"Finished sending. Success: {results['success']}, Failed: {results['failed']}")
        return results
