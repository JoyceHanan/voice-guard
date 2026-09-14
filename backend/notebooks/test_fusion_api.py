"""VoiceGuard Policy & Risk API End-to-End Validation Script.

Executes 4 comprehensive test scenarios against POST /analyze:
a) Real sample + Known caller -> Expect LOW risk, ALLOW action
b) Fake sample + Blocklisted caller + Suspicious context -> Expect CRITICAL risk, ESCALATE action
c) Real sample + Unknown neutral caller -> Expect LOW/MEDIUM risk
d) Noisy edge-case sample -> Verify SNR quality is MODERATE and observe risk impact
"""

import json
from pathlib import Path
import sys
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

API_URL = "http://127.0.0.1:8000/analyze"


def run_test_case(name: str, wav_path: Path, data_fields: dict):
    print("=" * 80)
    print(f"TEST CASE: {name}")
    print(f"Audio File: {wav_path.name}")
    print(f"Context Fields: {data_fields}")
    print("-" * 80)

    if not wav_path.exists():
        print(f"ERROR: Audio file not found at {wav_path}")
        return None

    with open(wav_path, "rb") as f:
        files = {"file": (wav_path.name, f, "audio/wav")}
        resp = requests.post(API_URL, data=data_fields, files=files)

    if resp.status_code == 200:
        res_json = resp.json()
        print(json.dumps(res_json, indent=2))
        return res_json
    else:
        print(f"HTTP Error {resp.status_code}: {resp.text}")
        return None


def main():
    print("=" * 80)
    print("VoiceGuard End-to-End Policy & Risk Fusion API Validation")
    print("=" * 80 + "\n")

    # a) Real sample, caller_number="+911234567890" (known), new_beneficiary=False, urgency=False -> Expect LOW, ALLOW
    res_a = run_test_case(
        "a) Real Sample + Known Caller (+911234567890)",
        DATA_DIR / "real" / "asvspoof_real_01.wav",
        {"caller_number": "+911234567890", "new_beneficiary": "false", "urgency": "false"},
    )
    pass_a = (
        res_a
        and res_a.get("risk_tier") == "LOW"
        and res_a.get("recommended_action", {}).get("action") == "ALLOW"
    )
    print(
        f"\n>> PASS/FAIL NOTE (Test A): {'[PASS]' if pass_a else '[FAIL]'} "
        f"Expected LOW risk / ALLOW action, got: Tier={res_a.get('risk_tier') if res_a else 'N/A'}, "
        f"Action={res_a.get('recommended_action', {}).get('action') if res_a else 'N/A'}\n"
    )

    # b) Fake sample, caller_number="+19998887777" (blocklist), new_beneficiary=True, urgency=True -> Expect CRITICAL, ESCALATE
    res_b = run_test_case(
        "b) Fake Sample + Blocklisted Fraud Caller (+19998887777)",
        DATA_DIR / "fake" / "fake_sample.wav",
        {"caller_number": "+19998887777", "new_beneficiary": "true", "urgency": "true"},
    )
    pass_b = (
        res_b
        and res_b.get("risk_tier") == "CRITICAL"
        and res_b.get("recommended_action", {}).get("action") == "ESCALATE"
    )
    print(
        f"\n>> PASS/FAIL NOTE (Test B): {'[PASS]' if pass_b else '[FAIL]'} "
        f"Expected CRITICAL risk / ESCALATE action, got: Tier={res_b.get('risk_tier') if res_b else 'N/A'}, "
        f"Action={res_b.get('recommended_action', {}).get('action') if res_b else 'N/A'}\n"
    )

    # c) Real sample, caller_number="+15550001111" (unknown_neutral), new_beneficiary=False, urgency=False -> Expect LOW/MEDIUM
    res_c = run_test_case(
        "c) Real Sample + Unknown Neutral Caller (+15550001111)",
        DATA_DIR / "real" / "asvspoof_real_01.wav",
        {"caller_number": "+15550001111", "new_beneficiary": "false", "urgency": "false"},
    )
    pass_c = res_c and res_c.get("risk_tier") in ["LOW", "MEDIUM"]
    print(
        f"\n>> PASS/FAIL NOTE (Test C): {'[PASS]' if pass_c else '[FAIL]'} "
        f"Expected LOW/MEDIUM risk, got: Tier={res_c.get('risk_tier') if res_c else 'N/A'}, "
        f"Action={res_c.get('recommended_action', {}).get('action') if res_c else 'N/A'}\n"
    )

    # d) Noisy edge-case file -> Confirm SNR is MODERATE
    res_d = run_test_case(
        "d) Noisy Edge-Case Audio Sample (real_noisy.wav)",
        DATA_DIR / "edge_cases" / "real_noisy.wav",
        {"caller_number": "+911234567890", "new_beneficiary": "false", "urgency": "false"},
    )
    snr_label = res_d.get("audio_quality", {}).get("label") if res_d else "N/A"
    snr_db = res_d.get("audio_quality", {}).get("snr_db") if res_d else "N/A"
    pass_d = res_d and snr_label == "MODERATE"
    print(
        f"\n>> PASS/FAIL NOTE (Test D): {'[PASS]' if pass_d else '[FAIL]'} "
        f"Expected audio quality MODERATE, got: Label={snr_label} ({snr_db} dB), Risk Tier={res_d.get('risk_tier') if res_d else 'N/A'}\n"
    )

    print("=" * 80)
    print("ALL END-TO-END POLICY & RISK TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
