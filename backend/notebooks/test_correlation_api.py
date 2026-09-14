"""Correlation Engine & Campaign Detection End-to-End Test.

1. Sends 3 separate high-risk /analyze requests with similar caller prefixes (+19998),
   similar voice scores (-4.66), and similar transaction amounts (~$5000).
2. Calls GET /correlation/check to verify multi-signal campaign alert triggering.
"""

import json
from pathlib import Path
import sys
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

BASE_URL = "http://127.0.0.1:8000"


def main():
    print("=" * 80)
    print("VoiceGuard Correlation Engine & Campaign Detection API Test")
    print("=" * 80 + "\n")

    fake_file = DATA_DIR / "fake" / "fake_sample.wav"
    if not fake_file.exists():
        print(f"ERROR: Audio file not found at {fake_file}")
        return

    test_calls = [
        {"caller_number": "+19998887701", "transaction_amount": 5000.00, "new_beneficiary": "true", "urgency": "true"},
        {"caller_number": "+19998887702", "transaction_amount": 5200.00, "new_beneficiary": "true", "urgency": "true"},
        {"caller_number": "+19998887703", "transaction_amount": 4800.00, "new_beneficiary": "true", "urgency": "true"},
    ]

    print("1. Sending 3 High-Risk Flagged Calls to /analyze...")
    print("-" * 80)

    for i, data in enumerate(test_calls, 1):
        with open(fake_file, "rb") as f:
            files = {"file": (fake_file.name, f, "audio/wav")}
            resp = requests.post(f"{BASE_URL}/analyze", data=data, files=files)
            if resp.status_code == 200:
                res_json = resp.json()
                print(f"Call {i} ({data['caller_number']}): Tier={res_json['risk_tier']}, Score={res_json['risk_score']}")
            else:
                print(f"Call {i} Error {resp.status_code}: {resp.text}")

    print("\n2. Calling GET /correlation/check...")
    print("-" * 80)
    r_corr = requests.get(f"{BASE_URL}/correlation/check")
    if r_corr.status_code == 200:
        corr_json = r_corr.json()
        print(json.dumps(corr_json, indent=2))
        alert_pass = corr_json.get("alert") is True
        print(f"\n>> PASS/FAIL NOTE (Correlation Alert): {'[PASS]' if alert_pass else '[FAIL]'} Expected alert=True, got: {corr_json.get('alert')}")
    else:
        print(f"Correlation Check Error {r_corr.status_code}: {r_corr.text}")

    print("=" * 80)


if __name__ == "__main__":
    main()
