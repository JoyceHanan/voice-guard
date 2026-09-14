"""VoiceGuard Active Verification Challenge Engine.

Generates random challenge phrases and verifies user spoken audio responses
using OpenAI Whisper speech-to-text transcription.
"""

import os
import random
import uuid
from pathlib import Path
import torch
import whisper

_WHISPER_MODEL = None
SAVEDIR = Path(__file__).resolve().parent / "models" / "whisper"

CHALLENGE_PHRASES = [
    "blue tiger seven",
    "bright solar system",
    "silver mountain stream",
    "golden sunset horizon",
    "swift crimson arrow",
    "crystal ocean wave",
]

# In-memory challenge store: { challenge_id: expected_phrase }
ACTIVE_CHALLENGES = {}


def load_whisper_model():
    """Load or retrieve cached Whisper speech-to-text model ('tiny' for fast inference)."""
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading OpenAI Whisper model ('tiny') on device: {device}...")
        _WHISPER_MODEL = whisper.load_model("tiny", device=device)
        print("Whisper model loaded successfully.")
    return _WHISPER_MODEL


def generate_challenge() -> dict:
    """Generates a random challenge phrase and stores it with a unique challenge_id.

    Returns:
        dict: {"challenge_id": str, "phrase": str, "prompt": str}
    """
    challenge_id = str(uuid.uuid4())
    phrase = random.choice(CHALLENGE_PHRASES)
    ACTIVE_CHALLENGES[challenge_id] = phrase

    return {
        "challenge_id": challenge_id,
        "phrase": phrase,
        "prompt": f"Please say: {phrase}",
    }


def verify_challenge_response(audio_file_path: str, expected_phrase: str) -> dict:
    """Transcribes audio file using Whisper STT and verifies matching against expected_phrase."""
    import soundfile as sf
    import librosa

    model = load_whisper_model()

    # Load audio array directly via soundfile to avoid ffmpeg subprocess requirement on Windows
    audio, sr = sf.read(audio_file_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

    # Transcribe 1D float32 numpy audio array
    device_is_cuda = torch.cuda.is_available()
    result = model.transcribe(audio, fp16=device_is_cuda)
    transcribed_text = (result.get("text") or "").strip()

    # Normalize texts for comparison
    def clean_text(text: str) -> str:
        return "".join(c.lower() for c in text if c.isalnum() or c.isspace()).strip()

    norm_transcribed = clean_text(transcribed_text)
    norm_expected = clean_text(expected_phrase)

    expected_words = norm_expected.split()
    if not expected_words:
        matched = False
        confidence = 0.0
    else:
        # Count expected words found in transcribed text
        matched_words = sum(1 for word in expected_words if word in norm_transcribed.split())
        confidence = round(float(matched_words / len(expected_words)), 2)

        # Stricter Security Threshold:
        # - For short phrases (<=3 words), require exact 100% word match (confidence == 1.0)
        # - For longer phrases (>3 words), require at least 0.85 confidence (85% word match)
        if len(expected_words) <= 3:
            matched = confidence >= 1.0
        else:
            matched = confidence >= 0.85

    return {
        "matched": matched,
        "transcribed_text": transcribed_text,
        "expected_phrase": expected_phrase,
        "confidence": confidence,
    }
