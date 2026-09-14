"""API Key Authentication Test Script.

Tests POST /analyze without X-API-Key (expects 401 Unauthorized)
and with X-API-Key (expects 200 OK).
"""

from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8000"
AUDIO_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "real" / "asvspoof_real_01.wav"
API_KEY = "vg_secret_key_12345"


def main():
    print("=" * 70)
    print("VoiceGuard API Key Authentication Verification")
    print("=" * 70)

    # 1. Request WITHOUT API key
    print("\n1. Testing Request WITHOUT X-API-Key Header...")
    with open(AUDIO_PATH, "rb") as f:
        r_no_key = requests.post(
            f"{BASE_URL}/analyze",
            files={"file": ("sample.wav", f, "audio/wav")},
        )
    print(f"Status Code: {r_no_key.status_code}")
    print(f"Response: {r_no_key.text}")
    assert r_no_key.status_code == 401, "Expected 401 Unauthorized"
    print("--> CONFIRMED: Request without key rejected with 401 Unauthorized.")

    # 2. Request WITH Invalid API key
    print("\n2. Testing Request WITH INVALID X-API-Key Header...")
    with open(AUDIO_PATH, "rb") as f:
        r_invalid_key = requests.post(
            f"{BASE_URL}/analyze",
            headers={"X-API-Key": "wrong_key_xyz"},
            files={"file": ("sample.wav", f, "audio/wav")},
        )
    print(f"Status Code: {r_invalid_key.status_code}")
    print(f"Response: {r_invalid_key.text}")
    assert r_invalid_key.status_code == 401, "Expected 401 Unauthorized"
    print("--> CONFIRMED: Request with invalid key rejected with 401 Unauthorized.")

    # 3. Request WITH Valid API key
    print("\n3. Testing Request WITH VALID X-API-Key Header...")
    with open(AUDIO_PATH, "rb") as f:
        r_valid = requests.post(
            f"{BASE_URL}/analyze",
            headers={"X-API-Key": API_KEY},
            files={"file": ("sample.wav", f, "audio/wav")},
        )
    print(f"Status Code: {r_valid.status_code}")
    print(f"Response: risk_tier={r_valid.json().get('risk_tier')}, voice_result={r_valid.json().get('voice_result')}")
    assert r_valid.status_code == 200, "Expected 200 OK"
    print("--> CONFIRMED: Request with valid key authorized successfully (200 OK).")

    print("\nAUTH VERIFICATION COMPLETE: ALL ASSERIONS PASSED.")


if __name__ == "__main__":
    main()
