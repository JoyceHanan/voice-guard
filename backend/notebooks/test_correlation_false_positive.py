"""VoiceGuard Correlation Engine False-Positive Benchmark Script.

Tests that logging 3 deliberately UNRELATED flagged calls (different caller prefixes,
different transaction amounts, and different voice scores) does NOT trigger a false alert (alert=False).
"""

import json
import sys
from pathlib import Path
import sqlite3
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "vg_secret_key_12345"
HEADERS = {"X-API-Key": API_KEY}
DB_PATH = BACKEND_DIR / "data" / "voiceguard.db"


def clear_flagged_calls():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM flagged_calls")
    conn.commit()
    conn.close()


def main():
    print("=" * 80)
    print("VoiceGuard Correlation Engine False-Positive Benchmark")
    print("=" * 80)

    # 1. Clear previous flagged calls history for isolated test
    print("\n1. Clearing previous flagged call history in SQLite...")
    clear_flagged_calls()

    # 2. Log 3 Deliberately Unrelated Calls
    print("\n2. Logging 3 Deliberately UNRELATED Flagged Calls...")

    # We will log 3 calls with different prefixes (+19998, +14443, +17776),
    # different transaction amounts ($5k, $50k, $250k), and different scores (-4.66, -2.10, +0.50)
    unrelated_calls = [
        {
            "caller_number": "+19998881001",
            "voice_score": -4.66,
            "risk_tier": "CRITICAL",
            "transaction_amount": 5000.0,
        },
        {
            "caller_number": "+14443332002",
            "voice_score": -2.10,
            "risk_tier": "CRITICAL",
            "transaction_amount": 50000.0,
        },
        {
            "caller_number": "+17776663003",
            "voice_score": 0.50,
            "risk_tier": "HIGH",
            "transaction_amount": 250000.0,
        },
    ]

    from storage import log_flagged_call_db
    for idx, call_data in enumerate(unrelated_calls, 1):
        log_flagged_call_db(call_data)
        print(f"   Call {idx} logged: Num='{call_data['caller_number']}', Score={call_data['voice_score']}, Amount=${call_data['transaction_amount']}")

    # 3. Check Correlation Engine Output
    print("\n3. Querying GET /correlation/check...")
    r_corr = requests.get(f"{BASE_URL}/correlation/check")
    res_corr = r_corr.json()
    print("Response:")
    print(json.dumps(res_corr, indent=2))

    alert_status = res_corr.get("alert")
    print(f"\n4. Correlation Alert Status: {alert_status}")
    if alert_status is False:
        print("--> CONFIRMED: No false positive triggered for unrelated flagged calls (alert=False).")
    else:
        print("--> WARNING: Unexpected alert triggered!")


if __name__ == "__main__":
    main()
