"""Active Verification Challenge Endpoints Test Script.

Tests POST /challenge/generate and POST /challenge/verify using Whisper STT:
1. Generates active challenge phrase.
2. Verifies matching spoken audio response -> Expect matched=True.
3. Verifies non-matching spoken audio response -> Expect matched=False.
"""

import io
import json
import os
from pathlib import Path
import sys
import requests
import soundfile as sf
import librosa
from gtts import gTTS

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "challenge_test"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:8000"


def generate_tts_wav(text: str, filename: str) -> Path:
    """Helper to generate a spoken 16kHz mono WAV file using gTTS."""
    tts = gTTS(text=text, lang="en", slow=False)
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    y, sr = librosa.load(mp3_fp, sr=16000, mono=True)
    out_path = DATA_DIR / filename
    sf.write(out_path, y, 16000, subtype="PCM_16")
    return out_path


def main():
    print("=" * 80)
    print("VoiceGuard Active Verification Challenge API Test (Whisper STT)")
    print("=" * 80 + "\n")

    # 1. Generate challenge
    r_gen = requests.post(f"{BASE_URL}/challenge/generate")
    if r_gen.status_code != 200:
        print(f"FAILED to generate challenge: {r_gen.text}")
        return

    gen_data = r_gen.json()
    challenge_id = gen_data["challenge_id"]
    phrase = gen_data["phrase"]

    print("1. GENERATED CHALLENGE:")
    print(json.dumps(gen_data, indent=2))
    print("-" * 80)

    # 2. Test Matching Response
    print(f"\n2. Testing MATCHING Response (Phrase: '{phrase}')...")
    match_wav = generate_tts_wav(phrase, "match_sample.wav")

    with open(match_wav, "rb") as f:
        r_match = requests.post(
            f"{BASE_URL}/challenge/verify",
            data={"challenge_id": challenge_id},
            files={"file": ("match_sample.wav", f, "audio/wav")},
        )

    res_match = r_match.json()
    print("Response:")
    print(json.dumps(res_match, indent=2))
    pass_match = res_match.get("matched") is True
    print(f">> PASS/FAIL NOTE (Matching Test): {'[PASS]' if pass_match else '[FAIL]'} Expected matched=True, got: {res_match.get('matched')}\n")

    # 3. Test Non-Matching Response
    different_phrase = "the quick brown fox jumps over the lazy dog"
    print(f"3. Testing NON-MATCHING Response (Spoken: '{different_phrase}')...")
    no_match_wav = generate_tts_wav(different_phrase, "no_match_sample.wav")

    # Re-generate challenge to avoid expired token if needed
    r_gen2 = requests.post(f"{BASE_URL}/challenge/generate")
    gen_data2 = r_gen2.json()
    challenge_id2 = gen_data2["challenge_id"]

    with open(no_match_wav, "rb") as f:
        r_no_match = requests.post(
            f"{BASE_URL}/challenge/verify",
            data={"challenge_id": challenge_id2},
            files={"file": ("no_match_sample.wav", f, "audio/wav")},
        )

    res_no_match = r_no_match.json()
    print("Response:")
    print(json.dumps(res_no_match, indent=2))
    pass_no_match = res_no_match.get("matched") is False
    print(f">> PASS/FAIL NOTE (Non-Matching Test): {'[PASS]' if pass_no_match else '[FAIL]'} Expected matched=False, got: {res_no_match.get('matched')}\n")

    print("=" * 80)
    print("ALL CHALLENGE ENGINE API TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
