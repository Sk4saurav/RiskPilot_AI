from typing import List, Dict, Any
from packages.domain import Evidence, Policy

class PolicyEngine:
    """
    Evaluates a set of Evidence against a configurable Organization Policy.
    """
    
    @classmethod
    def evaluate(cls, policy: Policy, evidence_set: List[Evidence]) -> int:
        """
        Calculates the risk score by mapping evidence types to configured weights.
        """
        if not policy or not policy.is_active:
            raise ValueError("No active policy provided for evaluation.")
            
        rules = policy.rules_config or {}
        total_score = 0
        
        for evidence in evidence_set:
            if evidence.evidence_type == "positive_history":
                matches = evidence.value.get("successful_matches", 0)
                tiers = rules.get("positive_history_tiers", {})
                
                if matches >= 5:
                    weight = tiers.get("5+", -15)
                elif matches >= 2:
                    weight = tiers.get("2-4", -10)
                elif matches == 1:
                    weight = tiers.get("1", -5)
                else:
                    weight = 0
                
                evidence.weight = weight
                # Apply negative weight, but don't drop below 0 risk.
                # Actually, wait. It's added to the total score, so a negative weight reduces it.
                total_score += weight
            else:
                # Use policy override weight if present, otherwise fallback to evidence base weight
                weight = rules.get(evidence.evidence_type, evidence.weight or 0)
                evidence.weight = weight
                total_score += weight
                
        # Ensure total score is between 0 and 100
        return max(0, min(total_score, 100))
    
    @classmethod
    def determine_severity(cls, policy: Policy, score: int, context: dict = None) -> tuple[str, str]:
        """
        Maps a 0-100 score to a severity category using dynamic policy thresholds.
        Evaluates conditions against a normalized context dictionary.
        Returns: (severity, rule_selected_rationale)
        """
        context = context or {}
        thresholds = policy.thresholds or {}
        rules = thresholds.get("rules", [])
        
        active_thresholds = None
        rule_rationale = "No dynamic rules defined, falling back to static thresholds."
        
        for i, rule in enumerate(rules):
            when = rule.get("when", {})
            
            if when.get("default"):
                active_thresholds = rule.get("severity_ranges")
                rule_rationale = f"Rule #{i+1} selected (default fallback)"
                break
                
            field = when.get("field")
            operator = when.get("operator")
            cond_val = when.get("value")
            
            if field in context:
                fact_val = context[field]
                match = False
                
                if operator == ">=" and fact_val >= cond_val:
                    match = True
                elif operator == "<" and fact_val < cond_val:
                    match = True
                elif operator == "==" and fact_val == cond_val:
                    match = True
                    
                if match:
                    active_thresholds = rule.get("severity_ranges")
                    rule_rationale = f"Rule #{i+1} selected (condition: {field} {operator} {cond_val}, actual: {fact_val})"
                    break
        
        if not active_thresholds:
            active_thresholds = {
                "LOW": [0, 29],
                "MEDIUM": [30, 59],
                "HIGH": [60, 79],
                "CRITICAL": [80, 100]
            }
            if rules:
                rule_rationale = "No matching dynamic rules or defaults found, falling back to static thresholds."
        
        for severity, (low, high) in active_thresholds.items():
            if low <= score <= high:
                return severity, rule_rationale
                
        return "UNKNOWN", rule_rationale
