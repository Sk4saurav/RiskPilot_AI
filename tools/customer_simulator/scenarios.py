from .generator import generate_normal_event, generate_suspicious_event, generate_critical_event, generate_false_positive_event
import random

def generate_scenario_batch(scenario: str, count: int):
    events = []
    
    if scenario == "normal":
        for _ in range(count):
            events.append(generate_normal_event())
    elif scenario == "suspicious":
        for _ in range(count):
            events.append(generate_suspicious_event())
    elif scenario == "critical":
        for i in range(count):
            evt = generate_critical_event()
            if i == 0:
                import uuid
                evt["event_id"] = f"TX-18492-{uuid.uuid4().hex[:4].upper()}" # Golden demo ID but unique
                evt["transaction"]["amount_cents"] = 28400000
            events.append(evt)
    elif scenario == "mixed":
        # E.g. 82% normal, 13% medium (suspicious), 5% critical
        for i in range(count):
            r = random.random()
            if r < 0.82:
                events.append(generate_normal_event())
            elif r < 0.95:
                events.append(generate_suspicious_event())
            else:
                evt = generate_critical_event()
                if not any(e.get("event_id") == "TX-18492" for e in events):
                    evt["event_id"] = "TX-18492"
                    evt["transaction"]["amount_cents"] = 28400000
                events.append(evt)
    elif scenario == "false_positive":
        for _ in range(count):
            events.append(generate_false_positive_event())
    else:
        raise ValueError(f"Unknown scenario: {scenario}")
        
    return events
