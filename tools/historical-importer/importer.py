import csv
import argparse
import asyncio
import httpx
import os

class HistoricalImporter:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-RiskPilot-Suppress-Webhooks": "true" # Custom header for replay
        }

    def map_customer_row_to_event(self, row: dict) -> dict:
        """
        The Integration Adapter logic: maps raw CSV row to canonical RiskPilot event.
        """
        return {
            "event_id": row.get("event_id"),
            "customer_id": row.get("customer_id"),
            "amount_cents": int(row.get("amount_cents", 0)),
            "currency": row.get("currency", "USD"),
            "location": {
                "city": row.get("location_city"),
                "country_code": row.get("location_country")
            },
            "device": {
                "is_new": row.get("device_is_new", "").lower() == "true"
            },
            "network": {
                "ip_address": row.get("ip_address")
            }
        }

    async def ingest_row(self, client: httpx.AsyncClient, row: dict, dataset_id: str):
        event_data = self.map_customer_row_to_event(row)
        
        payload = {
            "type": "transaction.created",
            "subject": row["event_id"],
            "data": event_data,
            "validation_metadata": {
                "manual_investigation_time_sec": int(row.get("manual_investigation_time_sec") or 0),
                "manual_analyst_time_sec": int(row.get("manual_analyst_time_sec") or 0),
                "manual_decision": row.get("manual_decision"),
                "manual_evidence_sources": row.get("manual_evidence_sources")
            }
        }
        
        try:
            resp = await client.post(
                f"{self.base_url}/v1/validation/datasets/{dataset_id}/import",
                json=payload,
                headers=self.headers,
                timeout=10.0
            )
            return resp.status_code == 200, resp.text
        except Exception as e:
            return False, str(e)

    async def run(self, csv_path: str):
        print(f"Importing historical data from {csv_path}...")
        
        # 1. Create dataset
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/v1/validation/datasets?name=Imported_Dataset",
                headers=self.headers
            )
            if resp.status_code != 200:
                print(f"Failed to create dataset: {resp.text}")
                return
            dataset_id = resp.json()["dataset_id"]
            print(f"Created Dataset: {dataset_id}")
        
        rows = []
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
                
        print(f"Found {len(rows)} records. Beginning import...")
        
        success = 0
        failed = 0
        
        # Concurrency limit
        semaphore = asyncio.Semaphore(20)
        
        async def bounded_ingest(client, row):
            nonlocal success, failed
            async with semaphore:
                ok, err = await self.ingest_row(client, row, dataset_id)
                if ok:
                    success += 1
                else:
                    failed += 1
                    print(f"Failed to ingest {row.get('event_id')}: {err}")
                    
        async with httpx.AsyncClient() as client:
            tasks = [bounded_ingest(client, row) for row in rows]
            await asyncio.gather(*tasks)
            
        print(f"Import Complete! Success: {success}, Failed: {failed}")
        print(f"To run replay, POST {self.base_url}/v1/validation/datasets/{dataset_id}/replay")

async def main():
    parser = argparse.ArgumentParser(description="Alpha 0.6 Historical Importer")
    parser.add_argument("--file", type=str, required=True, help="Path to historical_events.csv")
    parser.add_argument("--api-key", type=str, help="Customer API Key")
    parser.add_argument("--base-url", type=str, default="http://localhost:8000")
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("RISKPILOT_API_KEY")
    if not api_key:
        print("Error: --api-key required.")
        return
        
    importer = HistoricalImporter(api_key, args.base_url)
    await importer.run(args.file)

if __name__ == "__main__":
    asyncio.run(main())
