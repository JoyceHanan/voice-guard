"""VoiceGuard FastAPI REST Backend with WebSockets, SQLite Persistence, and API Key Auth.

Provides endpoints:
- POST /enroll : Enrolls a speaker embedding vector (Encrypted SQLite storage).
- GET /enrolled : Lists enrolled speaker IDs from SQLite.
- POST /analyze : Unified multi-factor risk assessment with caller classification & policy engine actions.
- WS /ws/analyze : Continuous real-time audio streaming assessment using a 4s sliding window (2s update hop).
- POST /challenge/generate : Generates a random active verification challenge phrase.
- POST /challenge/verify : Verifies audio response against challenge phrase using Whisper STT.
- GET /correlation/check : Scans flagged calls for multi-signal impersonation campaign clusters.
"""

from contextlib import asynccontextmanager
import io
import os
from pathlib import Path
import sys
import tempfile
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Header, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import soundfile as sf
import librosa
import torch

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "backend" / "models"
BACKEND_DIR = BASE_DIR / "backend"

sys.path.insert(0, str(MODEL_DIR / "aasist"))
sys.path.insert(0, str(MODEL_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from aasist_l import AASIST_L
from classifier import classify_with_quality_and_duration
from speaker_embed import compute_embedding, load_speaker_model
from audio_quality import estimate_quality
from fusion_engine import compute_risk
from policy_engine import get_recommended_action
from caller_registry import classify_caller
from challenge_engine import (
    generate_challenge,
    verify_challenge_response,
    ACTIVE_CHALLENGES,
)
from correlation_engine import log_flagged_call, check_correlation
from storage import (
    save_enrolled_speaker,
    load_enrolled_speakers,
    get_enrolled_speaker_ids,
)

RECOMMENDED_THRESHOLD = 2.10
MARGIN = 0.5
MODERATE_MARGIN = 1.2
MIN_DURATION = 4.0

# Load API key from backend/.env or default
ENV_FILE = BACKEND_DIR / ".env"
API_KEY = "vg_secret_key_12345"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if line.startswith("VOICEGUARD_API_KEY="):
            API_KEY = line.split("=", 1)[1].strip()

detector = None


async def verify_api_key(x_api_key: str = Header(None)):
    """FastAPI dependency to verify X-API-Key header on protected endpoints."""
    if not x_api_key or x_api_key.strip() != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global detector
    print(f"Loading AASIST-L detector from {MODEL_DIR / 'aasist'}...")
    detector = AASIST_L()
    detector.load()
    print("Loading SpeechBrain ECAPA-TDNN speaker embedder...")
    load_speaker_model()
    print("VoiceGuard models & SQLite database loaded successfully.")
    yield
    print("Shutting down VoiceGuard backend.")


app = FastAPI(
    title="VoiceGuard Deepfake & Multi-Factor Security Platform API",
    version="1.6.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "status": "online",
        "model": "AASIST-L",
        "speaker_embedder": "ECAPA-TDNN",
        "threshold": RECOMMENDED_THRESHOLD,
        "enrolled_count": len(get_enrolled_speaker_ids()),
    }


@app.get("/enrolled")
def get_enrolled_speakers():
    """Lists currently enrolled speaker IDs from SQLite."""
    return {"enrolled_speakers": get_enrolled_speaker_ids()}


@app.post("/enroll", dependencies=[Depends(verify_api_key)])
async def enroll_speaker(
    speaker_id: str = Form(...), file: UploadFile = File(...)
):
    """Enrolls a speaker by extracting and storing encrypted embedding in SQLite."""
    clean_id = speaker_id.strip()
    if not clean_id:
        raise HTTPException(status_code=400, detail="speaker_id must be a non-empty string.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty audio file provided.")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            temp_path = tmp.name

        emb = compute_embedding(temp_path)
        save_enrolled_speaker(clean_id, emb)

        return {
            "status": "enrolled",
            "speaker_id": clean_id,
            "message": f"Successfully enrolled speaker '{clean_id}' into encrypted SQLite database.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process enrollment audio: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/analyze", dependencies=[Depends(verify_api_key)])
async def analyze_audio(
    file: UploadFile = File(...),
    claimed_identity: str = Form(None),
    caller_number: str = Form(None),
    known_caller: bool = Form(False),
    new_beneficiary: bool = Form(False),
    urgency: bool = Form(False),
    transaction_amount: float = Form(0.0),
):
    """Unified multi-factor risk assessment endpoint with caller classification & policy engine actions."""
    if not detector:
        raise HTTPException(status_code=500, detail="Detector model not loaded.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty audio file provided.")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            temp_path = tmp.name

        audio, sr = sf.read(temp_path, dtype="float32")
        duration_seconds = float(len(audio) / sr)

        quality_label, snr_db = estimate_quality(audio, sr)

        if caller_number and caller_number.strip():
            caller_class = classify_caller(caller_number.strip())
        else:
            eff_cat = "known" if known_caller else "unknown_neutral"
            caller_class = {
                "category": eff_cat,
                "name": None,
                "reason": "Derived from boolean flag",
            }

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

        score = detector.score_batch([audio], [16000])[0]

        voice_result = classify_with_quality_and_duration(
            score,
            RECOMMENDED_THRESHOLD,
            duration_seconds=duration_seconds,
            audio_quality_label=quality_label,
            min_duration=MIN_DURATION,
            margin=MARGIN,
            moderate_margin=MODERATE_MARGIN,
        )

        speaker_similarity = None
        enrolled = load_enrolled_speakers()
        if claimed_identity and claimed_identity.strip() in enrolled:
            ref_emb = enrolled[claimed_identity.strip()]
            sample_emb = compute_embedding(temp_path)
            sim = torch.nn.functional.cosine_similarity(
                sample_emb.unsqueeze(0), ref_emb.unsqueeze(0)
            )
            speaker_similarity = round(float(sim.item()), 4)

        risk_fusion = compute_risk(
            voice_score=score,
            speaker_similarity=speaker_similarity,
            audio_quality_label=quality_label,
            duration_seconds=duration_seconds,
            known_caller=known_caller,
            caller_category=caller_class["category"],
            new_beneficiary=new_beneficiary,
            urgency=urgency,
            min_duration=MIN_DURATION,
        )

        if voice_result.startswith("INCONCLUSIVE") and risk_fusion["tier"] != "INCONCLUSIVE":
            risk_fusion["tier"] = "INCONCLUSIVE"
            risk_fusion["score"] = None
            risk_fusion["reason"] = f"Voice classification inconclusive: {voice_result}"

        # Automatically log flagged high-risk calls for correlation monitoring
        log_flagged_call({
            "caller_number": caller_number or "",
            "score": round(float(score), 2),
            "risk_tier": risk_fusion["tier"],
            "transaction_amount": transaction_amount,
        })

        rec_action = get_recommended_action(risk_fusion["tier"])

        return {
            "score": round(float(score), 2),
            "duration": round(duration_seconds, 2),
            "voice_result": voice_result,
            "speaker_similarity": speaker_similarity,
            "audio_quality": {
                "label": quality_label,
                "snr_db": snr_db,
            },
            "caller_classification": caller_class,
            "risk_tier": risk_fusion["tier"],
            "risk_score": risk_fusion["score"],
            "risk_reason": risk_fusion["reason"],
            "recommended_action": rec_action,
            "evidence_breakdown": risk_fusion["breakdown"],
            "threshold": RECOMMENDED_THRESHOLD,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error analyzing audio: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# --- WebSocket Real-Time Audio Streaming Endpoint ---

@app.websocket("/ws/analyze")
async def ws_analyze_stream(
    websocket: WebSocket,
    api_key: str = None,
    claimed_identity: str = None,
    caller_number: str = None,
    known_caller: bool = False,
    new_beneficiary: bool = False,
    urgency: bool = False,
    transaction_amount: float = 0.0,
):
    """Continuous WebSocket audio streaming endpoint using a sliding 4s window (2s update hop)."""
    await websocket.accept()

    req_key = api_key or websocket.headers.get("x-api-key")
    if not req_key or req_key.strip() != API_KEY:
        await websocket.send_json({"error": "Unauthorized: Invalid or missing API key."})
        await websocket.close(code=1008)
        return

    enrolled = load_enrolled_speakers()
    ref_emb = enrolled.get(claimed_identity.strip()) if claimed_identity and claimed_identity.strip() in enrolled else None

    audio_buffer = np.array([], dtype=np.float32)
    sample_rate = 16000
    target_samples = int(4.0 * sample_rate)  # 64,000 samples = 4.0s
    hop_samples = int(2.0 * sample_rate)     # 32,000 samples = 2.0s sliding window

    try:
        while True:
            data = await websocket.receive_bytes()
            if not data:
                continue

            # Load audio chunk bytes (supports WAV format or raw PCM float32)
            try:
                y_chunk, sr_chunk = sf.read(io.BytesIO(data), dtype="float32")
                if y_chunk.ndim > 1:
                    y_chunk = y_chunk.mean(axis=1)
                if sr_chunk != sample_rate:
                    y_chunk = librosa.resample(y_chunk, orig_sr=sr_chunk, target_sr=sample_rate)
            except Exception:
                # Fallback: assume raw float32 buffer
                y_chunk = np.frombuffer(data, dtype=np.float32)

            audio_buffer = np.concatenate([audio_buffer, y_chunk])

            # Check if buffer has reached 4.0s minimum requirement
            if len(audio_buffer) >= target_samples:
                window = audio_buffer[:target_samples]
                duration_sec = 4.0

                quality_label, snr_db = estimate_quality(window, sample_rate)
                score = float(detector.score_batch([window], [sample_rate])[0])

                voice_res = classify_with_quality_and_duration(
                    score,
                    RECOMMENDED_THRESHOLD,
                    duration_seconds=duration_sec,
                    audio_quality_label=quality_label,
                    min_duration=MIN_DURATION,
                    margin=MARGIN,
                    moderate_margin=MODERATE_MARGIN,
                )

                speaker_sim = None
                if ref_emb is not None:
                    # Temporary file for speaker embedding extraction
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                        sf.write(tmp.name, window, sample_rate, subtype="PCM_16")
                        tmp_name = tmp.name
                    try:
                        sample_emb = compute_embedding(tmp_name)
                        sim = torch.nn.functional.cosine_similarity(
                            sample_emb.unsqueeze(0), ref_emb.unsqueeze(0)
                        )
                        speaker_sim = round(float(sim.item()), 4)
                    finally:
                        if os.path.exists(tmp_name):
                            os.remove(tmp_name)

                caller_class = classify_caller(caller_number) if caller_number else {
                    "category": "known" if known_caller else "unknown_neutral",
                    "name": None,
                    "reason": "Streaming parameter",
                }

                risk_fusion = compute_risk(
                    voice_score=score,
                    speaker_similarity=speaker_sim,
                    audio_quality_label=quality_label,
                    duration_seconds=duration_sec,
                    known_caller=known_caller,
                    caller_category=caller_class["category"],
                    new_beneficiary=new_beneficiary,
                    urgency=urgency,
                    min_duration=MIN_DURATION,
                )

                rec_act = get_recommended_action(risk_fusion["tier"])

                response_payload = {
                    "status": "evaluated",
                    "window_duration": duration_sec,
                    "score": round(score, 2),
                    "voice_result": voice_res,
                    "speaker_similarity": speaker_sim,
                    "audio_quality": {"label": quality_label, "snr_db": snr_db},
                    "risk_tier": risk_fusion["tier"],
                    "risk_score": risk_fusion["score"],
                    "recommended_action": rec_act,
                }
                await websocket.send_json(response_payload)

                # Slide window: keep last 2s (32,000 samples)
                audio_buffer = audio_buffer[hop_samples:]
            else:
                curr_dur = round(len(audio_buffer) / sample_rate, 2)
                await websocket.send_json({
                    "status": "buffering",
                    "duration_accumulated": curr_dur,
                    "message": f"Accumulated {curr_dur}s / 4.0s minimum audio required...",
                })
    except WebSocketDisconnect:
        pass


# --- Challenge & Correlation Endpoints ---

@app.post("/challenge/generate", dependencies=[Depends(verify_api_key)])
def api_generate_challenge():
    """Generates a random active challenge phrase for user verification."""
    return generate_challenge()


@app.post("/challenge/verify", dependencies=[Depends(verify_api_key)])
async def api_verify_challenge(
    challenge_id: str = Form(...), file: UploadFile = File(...)
):
    """Verifies user spoken response against expected challenge phrase using Whisper STT."""
    clean_cid = challenge_id.strip()
    if clean_cid not in ACTIVE_CHALLENGES:
        raise HTTPException(status_code=404, detail=f"Invalid or expired challenge_id: '{clean_cid}'.")

    expected_phrase = ACTIVE_CHALLENGES[clean_cid]

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty audio file provided.")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            temp_path = tmp.name

        result = verify_challenge_response(temp_path, expected_phrase)
        result["challenge_id"] = clean_cid
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to verify challenge response: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/correlation/check")
def api_check_correlation():
    """Scans recent flagged calls for multi-signal impersonation campaign clusters in SQLite."""
    return check_correlation()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
