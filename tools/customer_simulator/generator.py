import random
import uuid
from datetime import datetime, timezone

def get_iso_timestamp():
    return datetime.now(timezone.utc).isoformat()

def generate_normal_event(customer_id="CUST-1042"):
    return {
        "event_id": f"TX-NORM-{uuid.uuid4().hex[:8]}",
        "event_type": "transaction",
        "timestamp": get_iso_timestamp(),
        "actor": {"user_id": customer_id},
        "transaction": {"amount_cents": random.randint(500, 3500) * 100, "currency": "INR"},
        "network": {"ip": "12.34.56.78"},
        "device": {"is_new": False, "type": "known"},
        "location": {"city": "Mumbai", "country": "IN"}
    }

def generate_suspicious_event(customer_id="CUST-1042"):
    return {
        "event_id": f"TX-SUSP-{uuid.uuid4().hex[:8]}",
        "event_type": "transaction",
        "timestamp": get_iso_timestamp(),
        "actor": {"user_id": customer_id},
        "transaction": {"amount_cents": random.randint(50000, 200000) * 100, "currency": "INR"},
        "network": {"ip": "95.163.1.2"},
        "device": {"is_new": True, "type": "unknown"},
        "location": {"city": "Moscow", "country": "RU"}
    }

def generate_critical_event(customer_id="CUST-1042"):
    return {
        "event_id": f"TX-CRIT-{uuid.uuid4().hex[:8]}",
        "event_type": "transaction",
        "timestamp": get_iso_timestamp(),
        "actor": {"user_id": customer_id},
        "transaction": {"amount_cents": random.randint(250000, 500000) * 100, "currency": "INR"},
        "network": {"ip": "104.28.1.1"}, # Typically proxy/suspicious
        "device": {"is_new": True, "type": "unknown"},
        "location": {"city": "Unknown", "country": "XX"}
    }

def generate_false_positive_event(customer_id="CUST-1042"):
    return {
        "event_id": f"TX-FPOS-{uuid.uuid4().hex[:8]}",
        "event_type": "transaction",
        "timestamp": get_iso_timestamp(),
        "actor": {"user_id": customer_id},
        "transaction": {"amount_cents": random.randint(500, 3500) * 100, "currency": "INR"}, # Normal amount
        "network": {"ip": "104.28.1.1"}, # Suspicious network
        "device": {"is_new": False, "type": "known"},
        "location": {"city": "Mumbai", "country": "IN"}
    }
