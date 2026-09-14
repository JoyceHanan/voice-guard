"""Persistence, Fernet Encryption, and SHA-256 Hashing Inspection Test Script.

1. Enrolls a speaker ('CFO_Rajesh').
2. Queries SQLite raw table directly to print raw ciphertext embedding and SHA-256 hashed phone numbers.
3. Tests persistence across server restarts.
"""

import json
from pathlib import Path
import sqlite3
import sys
import requests

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "vg_secret_key_12345"
HEADERS = {"X-API-Key": API_KEY}
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "voiceguard.db"
REAL_WAV = Path(__file__).resolve().parent.parent.parent / "data" / "real" / "asvspoof_real_01.wav"


def inspect_raw_sqlite():
    print("\n--- RAW SQLITE DATABASE INSPECTION (DIRECT READ) ---")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Inspect enrolled_speakers
    print("\n1. Table: enrolled_speakers (Raw Data):")
    rows = cursor.execute("SELECT speaker_id, hex(substr(embedding, 1, 32)) as sample_ciphertext, enrolled_at FROM enrolled_speakers").fetchall()
    for r in rows:
        print(f"   speaker_id: '{r['speaker_id']}'")
        print(f"   raw_embedding_ciphertext_prefix (HEX): {r['sample_ciphertext']}...")
        print(f"   enrolled_at: {r['enrolled_at']}")

    # Inspect known_contacts
    print("\n2. Table: known_contacts (Raw Data):")
    rows = cursor.execute("SELECT phone_number, name FROM known_contacts").fetchall()
    for r in rows:
        print(f"   raw_phone_hash (SHA-256): {r['phone_number']} -> Name: '{r['name']}'")

    # Inspect flagged_calls
    print("\n3. Table: flagged_calls (Raw Data):")
    rows = cursor.execute("SELECT id, caller_number, prefix_hash, voice_score, risk_tier, transaction_amount FROM flagged_calls").fetchall()
    for r in rows:
        print(f"   ID {r['id']}: raw_caller_hash='{r['caller_number']}', prefix_hash='{r['prefix_hash']}', score={r['voice_score']}, tier='{r['risk_tier']}', amt={r['transaction_amount']}")

    conn.close()
    print("----------------------------------------------------\n")


def main():
    print("=" * 80)
    print("VoiceGuard SQLite Persistence & Encryption/Hashing Test")
    print("=" * 80)

    # 1. Enroll speaker
    print("\n1. Enrolling speaker 'CFO_Rajesh' via POST /enroll...")
    with open(REAL_WAV, "rb") as f:
        r_enroll = requests.post(
            f"{BASE_URL}/enroll",
            headers=HEADERS,
            data={"speaker_id": "CFO_Rajesh"},
            files={"file": ("asvspoof_real_01.wav", f, "audio/wav")},
        )
    print(f"Enroll Response ({r_enroll.status_code}): {r_enroll.text}")

    # 2. Log a flagged call into SQLite
    print("\n2. Logging a flagged call via POST /analyze...")
    with open(REAL_WAV, "rb") as f:
        requests.post(
            f"{BASE_URL}/analyze",
            headers=HEADERS,
            data={
                "caller_number": "+19998889999",
                "known_caller": "false",
                "new_beneficiary": "true",
                "urgency": "true",
                "transaction_amount": 75000.0,
            },
            files={"file": ("asvspoof_real_01.wav", f, "audio/wav")},
        )

    # 3. Direct Raw Inspection
    inspect_raw_sqlite()

    # 4. State BEFORE Restart
    print("4. API State BEFORE Restart:")
    r_enrolled_before = requests.get(f"{BASE_URL}/enrolled")
    print("   GET /enrolled:", r_enrolled_before.json())
    r_corr_before = requests.get(f"{BASE_URL}/correlation/check")
    print("   GET /correlation/check total_flagged_calls:", r_corr_before.json().get("total_flagged_calls", len(r_corr_before.json().get("matched_calls", []))))

    print("\n[NOTE]: Server restart test will be verified when full_dry_run is executed!")


if __name__ == "__main__":
    main()
