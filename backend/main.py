"""VoiceGuard FastAPI REST Backend.

Provides endpoints:
- POST /enroll : Enrolls a speaker embedding vector.
- GET /enrolled : Lists enrolled speaker IDs.
- POST /analyze : Multi-factor risk assessment with caller classification & policy engine actions.
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
from classifier import classify_with_duration_check
from speaker_embed import compute_embedding, load_speaker_model
from audio_quality import estimate_quality
from fusion_engine import compute_risk
from policy_engine import get_recommended_action
from caller_registry import classify_caller

RECOMMENDED_THRESHOLD = 2.10
MARGIN = 0.5
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
    title="VoiceGuard Deepfake & Policy Risk Engine API",
    version="1.3.0",
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
        # Write to temporary file with explicit cleanup in finally block
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            temp_path = tmp.name

        # Extract speaker embedding
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
        # Privacy & Disk Hygiene: Immediately delete temporary file
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
        # Write to temporary file with explicit cleanup in finally block
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            temp_path = tmp.name

        # Read audio & duration
        audio, sr = sf.read(temp_path, dtype="float32")
        duration_seconds = float(len(audio) / sr)

        # Estimate audio quality & SNR
        quality_label, snr_db = estimate_quality(audio, sr)

        # Classify caller phone number if provided, else use known_caller boolean fallback
        if caller_number and caller_number.strip():
            caller_class = classify_caller(caller_number.strip())
        else:
            eff_cat = "known" if known_caller else "unknown_neutral"
            caller_class = {
                "category": eff_cat,
                "name": None,
                "reason": "Derived from boolean flag",
            }

        # Convert to mono if multi-channel
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Resample to 16kHz for AASIST-L
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

        # Compute AASIST-L score
        score = detector.score_batch([audio], [16000])[0]

        # Classify result with duration safety check
        voice_result = classify_with_duration_check(
            score,
            RECOMMENDED_THRESHOLD,
            duration_seconds=duration_seconds,
            min_duration=MIN_DURATION,
            margin=MARGIN,
        )

        # Compute speaker similarity if claimed_identity is provided and enrolled
        speaker_similarity = None
        if claimed_identity and claimed_identity.strip() in ENROLLED_SPEAKERS:
            ref_emb = ENROLLED_SPEAKERS[claimed_identity.strip()]
            sample_emb = compute_embedding(temp_path)
            sim = torch.nn.functional.cosine_similarity(
                sample_emb.unsqueeze(0), ref_emb.unsqueeze(0)
            )
            speaker_similarity = round(float(sim.item()), 4)

        # Multi-factor Risk Fusion Computation
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

        # Map risk tier to policy action
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
        # Privacy & Disk Hygiene: Immediately delete temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
