import requests
import io
import wave
import numpy as np

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"X-API-Key": "vg_secret_key_12345"}

def create_dummy_wav(duration_sec=4.0, sample_rate=16000):
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    # Generate 440 Hz tone
    audio_data = (0.3 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    wav_io.seek(0)
    return wav_io.getvalue()

def run_tests():
    print("=== VOICEGUARD FRONTEND-BACKEND INTEGRATION TESTS ===")
    
    # 1. Health check
    res_root = requests.get(f"{BASE_URL}/", headers=HEADERS)
    print(f"1. Health Check GET /: Status {res_root.status_code}")
    print("   Response:", res_root.json())
    assert res_root.status_code == 200
    
    # 2. Enrollment Flow
    dummy_wav = create_dummy_wav(3.0)
    files_enroll = {'file': ('test_speaker.wav', dummy_wav, 'audio/wav')}
    data_enroll = {'speaker_id': 'FrontendTestUser_001'}
    res_enroll = requests.post(f"{BASE_URL}/enroll", headers=HEADERS, data=data_enroll, files=files_enroll)
    print(f"\n2. Enrollment Flow POST /enroll: Status {res_enroll.status_code}")
    print("   Response:", res_enroll.json())
    assert res_enroll.status_code == 200
    
    res_enrolled = requests.get(f"{BASE_URL}/enrolled", headers=HEADERS)
    print(f"   Listing GET /enrolled: Status {res_enrolled.status_code}")
    print("   Response:", res_enrolled.json())
    assert res_enrolled.status_code == 200
    assert 'FrontendTestUser_001' in res_enrolled.json()['enrolled_speakers']
    
    # 3. File Upload Analysis Flow
    dummy_wav_long = create_dummy_wav(5.0)
    files_analyze = {'file': ('call_recording.wav', dummy_wav_long, 'audio/wav')}
    data_analyze = {
        'claimed_identity': 'FrontendTestUser_001',
        'caller_number': '+1 (555) 019-2834',
        'new_beneficiary': 'true',
        'urgency': 'true',
        'transaction_amount': '75000.0'
    }
    res_analyze = requests.post(f"{BASE_URL}/analyze", headers=HEADERS, data=data_analyze, files=files_analyze)
    print(f"\n3. Analysis Flow POST /analyze: Status {res_analyze.status_code}")
    print("   Keys in response:", list(res_analyze.json().keys()))
    print("   Risk Score:", res_analyze.json().get('risk_score'))
    print("   Risk Tier:", res_analyze.json().get('risk_tier'))
    print("   Recommended Action:", res_analyze.json().get('recommended_action'))
    assert res_analyze.status_code == 200
    
    # 4. Challenge Generation & Verification Flow
    res_chal_gen = requests.post(f"{BASE_URL}/challenge/generate", headers=HEADERS)
    print(f"\n4. Challenge Generation POST /challenge/generate: Status {res_chal_gen.status_code}")
    chal_data = res_chal_gen.json()
    print("   Challenge ID:", chal_data.get('challenge_id'))
    print("   Phrase:", chal_data.get('phrase'))
    assert res_chal_gen.status_code == 200
    
    files_verify = {'file': ('response.wav', dummy_wav, 'audio/wav')}
    data_verify = {'challenge_id': chal_data['challenge_id']}
    res_chal_ver = requests.post(f"{BASE_URL}/challenge/verify", headers=HEADERS, data=data_verify, files=files_verify)
    print(f"   Challenge Verification POST /challenge/verify: Status {res_chal_ver.status_code}")
    print("   Response:", res_chal_ver.json())
    assert res_chal_ver.status_code == 200
    
    # 5. Correlation Check Flow
    res_corr = requests.get(f"{BASE_URL}/correlation/check", headers=HEADERS)
    print(f"\n5. Correlation Check GET /correlation/check: Status {res_corr.status_code}")
    print("   Response:", res_corr.json())
    assert res_corr.status_code == 200
    
    print("\nALL 4 FRONTEND-BACKEND INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
