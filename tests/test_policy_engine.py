import pytest
from packages.domain import Policy
from packages.risk_engine.evaluation.engine import PolicyEngine

def get_policy():
    thresholds = {
        "rules": [
            {
                "when": {"field": "amount_cents", "operator": ">=", "value": 500000},
                "severity_ranges": {"LOW": [0, 20], "MEDIUM": [21, 40], "HIGH": [41, 79], "CRITICAL": [80, 100]}
            },
            {
                "when": {"field": "amount_cents", "operator": "<", "value": 500000},
                "severity_ranges": {"LOW": [0, 49], "MEDIUM": [50, 79], "HIGH": [80, 89], "CRITICAL": [90, 100]}
            },
            {
                "when": {"default": True},
                "severity_ranges": {"LOW": [0, 49], "MEDIUM": [50, 79], "HIGH": [80, 89], "CRITICAL": [90, 100]}
            }
        ]
    }
    return Policy(id="pol_test", organization_id="org_1", name="Test", is_active=True, rules_config={}, thresholds=thresholds, version=1)

def test_rule_selection():
    policy = get_policy()
    
    # Low-value threshold
    sev, rat = PolicyEngine.determine_severity(policy, 60, context={"amount_cents": 1000})
    assert sev == "MEDIUM"
    assert "Rule #2 selected" in rat
    
    # High-value threshold
    sev, rat = PolicyEngine.determine_severity(policy, 60, context={"amount_cents": 500000})
    assert sev == "HIGH"
    assert "Rule #1 selected" in rat

def test_boundaries():
    policy = get_policy()
    
    # Boundary: amount = 499999, score = 40
    sev, _ = PolicyEngine.determine_severity(policy, 40, context={"amount_cents": 499999})
    assert sev == "LOW"
    
    # Boundary: amount = 499999, score = 50
    sev, _ = PolicyEngine.determine_severity(policy, 50, context={"amount_cents": 499999})
    assert sev == "MEDIUM"

    # Boundary: amount = 500000, score = 40
    sev, rat = PolicyEngine.determine_severity(policy, 40, context={"amount_cents": 500000})
    assert sev == "MEDIUM"
    
    # Boundary: amount = 500000, score = 41
    sev, rat = PolicyEngine.determine_severity(policy, 41, context={"amount_cents": 500000})
    assert sev == "HIGH"
    
    # Boundary: amount = 500001, score = 41
    sev, _ = PolicyEngine.determine_severity(policy, 41, context={"amount_cents": 500001})
    assert sev == "HIGH"

def test_missing_context():
    policy = get_policy()
    
    # Missing amount_cents entirely
    sev, rat = PolicyEngine.determine_severity(policy, 60, context={"currency": "USD"})
    assert sev == "MEDIUM"
    assert "default fallback" in rat
    
    # Empty context
    sev, rat = PolicyEngine.determine_severity(policy, 60, context={})
    assert sev == "MEDIUM"
    assert "default fallback" in rat

def test_score_boundaries():
    policy = get_policy()
    
    sev, rat = PolicyEngine.determine_severity(policy, 20, context={"amount_cents": 500000})
    assert sev == "LOW"
    sev, rat = PolicyEngine.determine_severity(policy, 21, context={"amount_cents": 500000})
    assert sev == "MEDIUM"
    sev, rat = PolicyEngine.determine_severity(policy, 40, context={"amount_cents": 500000})
    assert sev == "MEDIUM"
    sev, rat = PolicyEngine.determine_severity(policy, 41, context={"amount_cents": 500000})
    assert sev == "HIGH"
    sev, rat = PolicyEngine.determine_severity(policy, 79, context={"amount_cents": 500000})
    assert sev == "HIGH"
    sev, rat = PolicyEngine.determine_severity(policy, 80, context={"amount_cents": 500000})
    assert sev == "CRITICAL"
    sev, rat = PolicyEngine.determine_severity(policy, 89, context={"amount_cents": 1000})
    assert sev == "HIGH"
    sev, rat = PolicyEngine.determine_severity(policy, 90, context={"amount_cents": 1000})
    assert sev == "CRITICAL"
