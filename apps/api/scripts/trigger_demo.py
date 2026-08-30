import requests

# This script triggers the RiskPilot AI workflow for the Hackathon Demo
print("Triggering TX-18492 through the Detection Engine...")

payload = {
    "id": "TX-18492",
    "customer_id": "ade6b26e-b6d0-460a-aa95-674626b2310f",
    "amount": 284000.0,
    "currency": "INR",
    "location": "Moscow, RUS",
    "ip_address": "203.0.113.42",
    "device_id": "dev_unknown_android"
}

try:
    response = requests.post("http://localhost:8000/api/events/ingest", json=payload)
    if response.status_code in [200, 202]:
        print("\n✅ Success! TX-18492 ingested. The AI Agents are now investigating in the background.")
        print("Switch to your browser dashboard to view the live investigation!")
    else:
        print(f"\n⚠️ API Response ({response.status_code}): {response.text}")
except Exception as e:
    print(f"\n❌ Failed to connect to the backend: {e}")
