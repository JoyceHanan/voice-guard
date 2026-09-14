"""VoiceGuard End-to-End Dry-Run Simulation Script.

Simulates the complete end-to-end fraud call defense workflow with API Key auth:
1. Speaker Enrollment (CFO_Rajesh into Encrypted SQLite)
2. Challenge Phrase Generation
3. Legitimate Call Analysis (Low Risk / ALLOW)
4. Fraud Call Analysis (Critical Risk / ESCALATE)
5. Challenge Verification:
   a) Deliberate Wrong Answer -> matched=False
   b) Correct Phrase Answer -> matched=True
6. Repeated Fraud Calls (Building Flagged Call History in SQLite)
7. Campaign Correlation Cluster Detection
8. Comprehensive Verification Summary
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
REAL_WAV = BASE_DIR / "data" / "real" / "asvspoof_real_01.wav"
FAKE_WAV = BASE_DIR / "data" / "fake" / "fake_sample.wav"
FAKE_WAV_2 = BASE_DIR / "data" / "fake" / "asvspoof_fake_02.wav"
FAKE_WAV_3 = BASE_DIR / "data" / "multilingual" / "fake" / "hindi_01.wav"
WRONG_ANSWER_WAV = BASE_DIR / "data" / "challenge_test" / "deliberate_wrong_answer.wav"

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "vg_secret_key_12345"
HEADERS = {"X-API-Key": API_KEY}


def generate_tts_wav_bytes(text: str) -> bytes:
    """Helper to generate spoken WAV bytes for a given text phrase using gTTS."""
    tts = gTTS(text=text, lang="en", slow=False)
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    y, sr = librosa.load(mp3_fp, sr=16000, mono=True)
    out_fp = io.BytesIO()
    sf.write(out_fp, y, 16000, format="WAV", subtype="PCM_16")
    return out_fp.getvalue()


def main():
    print("=" * 90)
    print("VoiceGuard Full End-to-End Dry-Run Simulation (Authenticated & Persistent)")
    print("=" * 90 + "\n")

    results_summary = []

    # -------------------------------------------------------------------------
    # STEP 1: POST /enroll — Enroll reference voice for "CFO_Rajesh"
    # -------------------------------------------------------------------------
    print("STEP 1: Enrolling Reference Voice Sample for 'CFO_Rajesh'...")
    with open(REAL_WAV, "rb") as f:
        r1 = requests.post(
            f"{BASE_URL}/enroll",
            headers=HEADERS,
            data={"speaker_id": "CFO_Rajesh"},
            files={"file": ("real_sample.wav", f, "audio/wav")},
        )
    step1_pass = False
    if r1.status_code == 200:
        res1 = r1.json()
        print(f"Response (Status {r1.status_code}):")
        print(json.dumps(res1, indent=2))
        if res1.get("status") == "enrolled" and res1.get("speaker_id") == "CFO_Rajesh":
            step1_pass = True
    else:
        print(f"ERROR Step 1: {r1.text}")

    results_summary.append({
        "step": "1. Voice Enrollment (/enroll)",
        "expected": "status='enrolled', speaker_id='CFO_Rajesh'",
        "actual": f"Status {r1.status_code}, enrolled={step1_pass}",
        "pass": step1_pass,
    })
    print("-" * 90 + "\n")

    # -------------------------------------------------------------------------
    # STEP 2: POST /challenge/generate — Generate Active Challenge Phrase
    # -------------------------------------------------------------------------
    print("STEP 2: Generating Active Verification Challenge Phrase...")
    r2 = requests.post(f"{BASE_URL}/challenge/generate", headers=HEADERS)
    step2_pass = False
    challenge_id = None
    expected_phrase = None
    if r2.status_code == 200:
        res2 = r2.json()
        print(f"Response (Status {r2.status_code}):")
        print(json.dumps(res2, indent=2))
        challenge_id = res2.get("challenge_id")
        expected_phrase = res2.get("phrase")
        if challenge_id and expected_phrase:
            step2_pass = True
    else:
        print(f"ERROR Step 2: {r2.text}")

    results_summary.append({
        "step": "2. Challenge Generation (/challenge/generate)",
        "expected": "Valid challenge_id and 3-word phrase",
        "actual": f"ID={challenge_id}, phrase='{expected_phrase}'",
        "pass": step2_pass,
    })
    print("-" * 90 + "\n")

    # -------------------------------------------------------------------------
    # STEP 3: POST /analyze — Simulate INCOMING LEGITIMATE Call
    # -------------------------------------------------------------------------
    print("STEP 3: Simulating Legitimate Call (Known CFO number, genuine voice, low urgency)...")
    with open(REAL_WAV, "rb") as f:
        r3 = requests.post(
            f"{BASE_URL}/analyze",
            headers=HEADERS,
            data={
                "claimed_identity": "CFO_Rajesh",
                "caller_number": "+911234567890",  # Known trusted contact
                "known_caller": "true",
                "new_beneficiary": "false",
                "urgency": "false",
                "transaction_amount": 5000.0,
            },
            files={"file": ("real_sample.wav", f, "audio/wav")},
        )
    step3_pass = False
    if r3.status_code == 200:
        res3 = r3.json()
        print(f"Response (Status {r3.status_code}):")
        print(json.dumps(res3, indent=2))
        tier = res3.get("risk_tier")
        action = res3.get("recommended_action", {}).get("action")
        if tier == "LOW" and action == "ALLOW":
            step3_pass = True
    else:
        print(f"ERROR Step 3: {r3.text}")

    results_summary.append({
        "step": "3. Legitimate Call Assessment (/analyze)",
        "expected": "risk_tier='LOW', recommended_action='ALLOW'",
        "actual": f"tier={res3.get('risk_tier') if r3.status_code == 200 else 'ERR'}, action={res3.get('recommended_action', {}).get('action') if r3.status_code == 200 else 'ERR'}",
        "pass": step3_pass,
    })
    print("-" * 90 + "\n")

    # -------------------------------------------------------------------------
    # STEP 4: POST /analyze — Simulate FRAUD Scenario (Core Demo Moment)
    # -------------------------------------------------------------------------
    print("STEP 4: Simulating Fraud Scenario (Synthetic voice, claimed CFO, unknown number, high urgency)...")
    with open(FAKE_WAV, "rb") as f:
        r4 = requests.post(
            f"{BASE_URL}/analyze",
            headers=HEADERS,
            data={
                "claimed_identity": "CFO_Rajesh",
                "caller_number": "+19998881001",  # Unknown spoofed number
                "known_caller": "false",
                "new_beneficiary": "true",
                "urgency": "true",
                "transaction_amount": 50000.0,
            },
            files={"file": ("fake_sample.wav", f, "audio/wav")},
        )
    step4_pass = False
    if r4.status_code == 200:
        res4 = r4.json()
        print(f"Response (Status {r4.status_code}):")
        print(json.dumps(res4, indent=2))
        tier4 = res4.get("risk_tier")
        action4 = res4.get("recommended_action", {}).get("action")
        if tier4 in ["HIGH", "CRITICAL"] and action4 in ["VERIFY", "ESCALATE"]:
            step4_pass = True
    else:
        print(f"ERROR Step 4: {r4.text}")

    results_summary.append({
        "step": "4. Fraud Call Assessment (/analyze)",
        "expected": "risk_tier='CRITICAL' (or 'HIGH'), recommended_action='ESCALATE' (or 'VERIFY')",
        "actual": f"tier={res4.get('risk_tier') if r4.status_code == 200 else 'ERR'}, action={res4.get('recommended_action', {}).get('action') if r4.status_code == 200 else 'ERR'}",
        "pass": step4_pass,
    })
    print("-" * 90 + "\n")

    # -------------------------------------------------------------------------
    # STEP 5a: POST /challenge/verify — Deliberate Wrong-Answer Challenge Test
    # -------------------------------------------------------------------------
    print("STEP 5a: Simulating Caller Submitting DELIBERATE WRONG ANSWER to Challenge...")
    with open(WRONG_ANSWER_WAV, "rb") as f:
        r5a = requests.post(
            f"{BASE_URL}/challenge/verify",
            headers=HEADERS,
            data={"challenge_id": challenge_id},
            files={"file": ("deliberate_wrong_answer.wav", f, "audio/wav")},
        )
    step5a_pass = False
    if r5a.status_code == 200:
        res5a = r5a.json()
        print(f"Response (Status {r5a.status_code}):")
        print(json.dumps(res5a, indent=2))
        if res5a.get("matched") is False:
            step5a_pass = True
    else:
        print(f"ERROR Step 5a: {r5a.text}")

    results_summary.append({
        "step": "5a. Challenge Failure Test (Wrong Answer)",
        "expected": "matched=False, confidence < 1.0",
        "actual": f"matched={res5a.get('matched') if r5a.status_code == 200 else 'ERR'}, confidence={res5a.get('confidence') if r5a.status_code == 200 else 'ERR'}",
        "pass": step5a_pass,
    })
    print("-" * 90 + "\n")

    # -------------------------------------------------------------------------
    # STEP 5b: POST /challenge/verify — Deliberate Correct-Answer Challenge Test
    # -------------------------------------------------------------------------
    print(f"STEP 5b: Simulating Caller Submitting CORRECT ANSWER ('{expected_phrase}')...")
    # Generate fresh challenge ID for step 5b
    r2b = requests.post(f"{BASE_URL}/challenge/generate", headers=HEADERS).json()
    cid_b = r2b["challenge_id"]
    phrase_b = r2b["phrase"]

    correct_wav_bytes = generate_tts_wav_bytes(phrase_b)
    r5b = requests.post(
        f"{BASE_URL}/challenge/verify",
        headers=HEADERS,
        data={"challenge_id": cid_b},
        files={"file": ("correct_answer.wav", correct_wav_bytes, "audio/wav")},
    )
    step5b_pass = False
    if r5b.status_code == 200:
        res5b = r5b.json()
        print(f"Response (Status {r5b.status_code}):")
        print(json.dumps(res5b, indent=2))
        if res5b.get("matched") is True:
            step5b_pass = True
    else:
        print(f"ERROR Step 5b: {r5b.text}")

    results_summary.append({
        "step": "5b. Challenge Success Test (Correct Answer)",
        "expected": "matched=True, confidence >= 1.0",
        "actual": f"matched={res5b.get('matched') if r5b.status_code == 200 else 'ERR'}, confidence={res5b.get('confidence') if r5b.status_code == 200 else 'ERR'}",
        "pass": step5b_pass,
    })
    print("-" * 90 + "\n")

    # -------------------------------------------------------------------------
    # STEP 6: Repeat Fraud Calls 2 More Times (Build Flagged Call History)
    # -------------------------------------------------------------------------
    print("STEP 6: Simulating 2 Additional Flagged Fraud Calls (Campaign Pattern)...")
    
    # Fraud Call 2
    with open(FAKE_WAV_2, "rb") as f:
        r6_1 = requests.post(
            f"{BASE_URL}/analyze",
            headers=HEADERS,
            data={
                "claimed_identity": "CFO_Rajesh",
                "caller_number": "+19998881002",
                "known_caller": "false",
                "new_beneficiary": "true",
                "urgency": "true",
                "transaction_amount": 52000.0,
            },
            files={"file": ("asvspoof_fake_02.wav", f, "audio/wav")},
        )
    print("Fraud Call 2 Status:", r6_1.status_code, "Tier:", r6_1.json().get("risk_tier") if r6_1.status_code == 200 else "ERR")

    # Fraud Call 3
    with open(FAKE_WAV_3, "rb") as f:
        r6_2 = requests.post(
            f"{BASE_URL}/analyze",
            headers=HEADERS,
            data={
                "claimed_identity": "CFO_Rajesh",
                "caller_number": "+19998881003",
                "known_caller": "false",
                "new_beneficiary": "true",
                "urgency": "true",
                "transaction_amount": 48000.0,
            },
            files={"file": ("hindi_01.wav", f, "audio/wav")},
        )
    print("Fraud Call 3 Status:", r6_2.status_code, "Tier:", r6_2.json().get("risk_tier") if r6_2.status_code == 200 else "ERR")

    step6_pass = (
        r6_1.status_code == 200
        and r6_1.json().get("risk_tier") in ["HIGH", "CRITICAL"]
        and r6_2.status_code == 200
        and r6_2.json().get("risk_tier") in ["HIGH", "CRITICAL"]
    )
    results_summary.append({
        "step": "6. Repeated Fraud Calls (Campaign History)",
        "expected": "2 additional calls logged into flagged history with HIGH/CRITICAL risk",
        "actual": f"Call 2 tier={r6_1.json().get('risk_tier')}, Call 3 tier={r6_2.json().get('risk_tier')}",
        "pass": step6_pass,
    })
    print("-" * 90 + "\n")

    # -------------------------------------------------------------------------
    # STEP 7: GET /correlation/check — Check Coordinated Campaign Alert
    # -------------------------------------------------------------------------
    print("STEP 7: Checking Correlation Engine for Coordinated Impersonation Campaign...")
    r7 = requests.get(f"{BASE_URL}/correlation/check")
    step7_pass = False
    if r7.status_code == 200:
        res7 = r7.json()
        print(f"Response (Status {r7.status_code}):")
        print(json.dumps(res7, indent=2))
        if res7.get("alert") is True and len(res7.get("matched_calls", [])) >= 3:
            step7_pass = True
    else:
        print(f"ERROR Step 7: {r7.text}")

    results_summary.append({
        "step": "7. Campaign Correlation Alert (/correlation/check)",
        "expected": "alert=True, 3+ matched calls, 2+ signals aligned",
        "actual": f"alert={res7.get('alert') if r7.status_code == 200 else 'ERR'}, matched_count={len(res7.get('matched_calls', [])) if r7.status_code == 200 else 'ERR'}",
        "pass": step7_pass,
    })
    print("-" * 90 + "\n")

    # -------------------------------------------------------------------------
    # STEP 8: FINAL SUMMARY SECTION
    # -------------------------------------------------------------------------
    print("=" * 90)
    print("STEP 8: FULL DRY RUN EXECUTION SUMMARY")
    print("=" * 90)
    print(f"{'Step':<50} {'Expected':<30} {'Result':<10}")
    print("-" * 90)

    all_passed = True
    for item in results_summary:
        status_str = "PASS" if item["pass"] else "FAIL"
        if not item["pass"]:
            all_passed = False
        print(f"{item['step']:<50} {item['expected'][:28]:<30} {status_str:<10}")

    print("-" * 90)
    final_verdict = "OVERALL VERDICT: PASS" if all_passed else "OVERALL VERDICT: FAIL"
    print(f"\n>>> {final_verdict} <<<\n")


if __name__ == "__main__":
    main()
