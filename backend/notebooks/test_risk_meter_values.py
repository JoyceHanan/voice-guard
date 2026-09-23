import json

# Test cases for Task 1: Risk score display logic verification
test_cases = [
    {"input_score": None, "input_tier": None, "expected_score_display": "--", "expected_tier": "AWAITING ANALYSIS"},
    {"input_score": 5.2, "input_tier": "LOW", "expected_score_display": "5", "expected_tier": "LOW RISK TIER"},
    {"input_score": 22.14, "input_tier": "LOW", "expected_score_display": "22", "expected_tier": "LOW RISK TIER"},
    {"input_score": 50.0, "input_tier": "MEDIUM", "expected_score_display": "50", "expected_tier": "MEDIUM RISK TIER"},
    {"input_score": 90.4, "input_tier": "CRITICAL", "expected_score_display": "90", "expected_tier": "CRITICAL RISK TIER"}
]

def format_risk_meter(risk_score, risk_tier):
    is_evaluated = risk_score is not None
    numeric_score = float(risk_score) if is_evaluated else 0.0
    safe_score = min(100.0, max(0.0, numeric_score))
    norm_tier = (risk_tier or "LOW").upper() if is_evaluated else "AWAITING"
    
    score_display = str(round(safe_score)) if is_evaluated else "--"
    tier_display = f"{norm_tier} RISK TIER" if is_evaluated else "AWAITING ANALYSIS"
    
    return score_display, tier_display

print("=== RISK METER DISPLAY LOGIC TEST ===")
for case in test_cases:
    s_disp, t_disp = format_risk_meter(case["input_score"], case["input_tier"])
    pass_score = s_disp == case["expected_score_display"]
    pass_tier = t_disp == case["expected_tier"]
    status = "PASS" if (pass_score and pass_tier) else "FAIL"
    print(f"Input: risk_score={case['input_score']}, risk_tier={case['input_tier']} => Rendered Score: '{s_disp}', Rendered Tier: '{t_disp}' [{status}]")
