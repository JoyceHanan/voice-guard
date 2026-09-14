"""VoiceGuard FastAPI REST Backend.

Provides endpoints:
- POST /enroll : Enrolls a speaker embedding vector.
- GET /enrolled : Lists enrolled speaker IDs.
- POST /analyze : Multi-factor risk assessment with caller classification & policy engine actions.
- POST /challenge/generate : Generates a random active verification challenge phrase.
- POST /challenge/verify : Verifies audio response against challenge phrase using Whisper STT.
"""

import io
import os
from pathlib import Path
import sys
import tempfile
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
    load_whisper_model,
)

RECOMMENDED_THRESHOLD = 2.10
MARGIN = 0.5
MODERATE_MARGIN = 1.2
MIN_DURATION = 4.0

detector = None

# In-memory store for enrolled speaker embeddings: { speaker_id: torch.Tensor }
ENROLLED_SPEAKERS = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global detector
    print(f"Loading AASIST-L detector from {MODEL_DIR / 'aasist'}...")
    detector = AASIST_L()
    detector.load()
    print("Loading SpeechBrain ECAPA-TDNN speaker embedder...")
    load_speaker_model()
    print("VoiceGuard models loaded successfully.")
    yield
    print("Shutting down VoiceGuard backend.")


app = FastAPI(
    title="VoiceGuard Deepfake & Active Challenge API",
    version="1.4.0",
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
        "enrolled_count": len(ENROLLED_SPEAKERS),
    }


@app.get("/enrolled")
def get_enrolled_speakers():
    """Lists currently enrolled speaker IDs."""
    return {"enrolled_speakers": list(ENROLLED_SPEAKERS.keys())}


@app.post("/enroll")
async def enroll_speaker(
    speaker_id: str = Form(...), file: UploadFile = File(...)
):
    """Enrolls a speaker by extracting and storing their speaker embedding."""
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
        ENROLLED_SPEAKERS[clean_id] = emb

        return {
            "status": "enrolled",
            "speaker_id": clean_id,
            "message": f"Successfully enrolled speaker '{clean_id}'.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process enrollment audio: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    claimed_identity: str = Form(None),
    caller_number: str = Form(None),
    known_caller: bool = Form(False),
    new_beneficiary: bool = Form(False),
    urgency: bool = Form(False),
):
    """Unified multi-factor risk assessment endpoint with action policy recommendation."""
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

        # Estimate audio quality & SNR
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

        # Classify result with duration check and dynamic quality margin widening
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
        if claimed_identity and claimed_identity.strip() in ENROLLED_SPEAKERS:
            ref_emb = ENROLLED_SPEAKERS[claimed_identity.strip()]
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

        # Override risk tier if dynamic margin classified voice as INCONCLUSIVE
        if voice_result.startswith("INCONCLUSIVE") and risk_fusion["tier"] != "INCONCLUSIVE":
            risk_fusion["tier"] = "INCONCLUSIVE"
            risk_fusion["score"] = None
            risk_fusion["reason"] = f"Voice classification inconclusive: {voice_result}"

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


# --- Challenge Engine Endpoints ---

@app.post("/challenge/generate")
def api_generate_challenge():
    """Generates a random active challenge phrase for user verification."""
    return generate_challenge()


@app.post("/challenge/verify")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
