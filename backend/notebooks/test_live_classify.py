"""VoiceGuard Live Audio Classification Script.

Loads the AASIST-L model, runs inference on a target audio WAV file,
applies decision threshold classification with buffer margin, and outputs
the classification result and score.

Usage:
    python backend/notebooks/test_live_classify.py <path_to_audio.wav>
"""

import os
import sys
from pathlib import Path
import soundfile as sf
import librosa

# Configure paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "backend" / "models" / "aasist"
BACKEND_DIR = BASE_DIR / "backend"

sys.path.insert(0, str(MODEL_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from aasist_l import AASIST_L
from classifier import classify, classify_with_duration_check

# Recommended decision threshold from optimization (Task 1)
RECOMMENDED_THRESHOLD = 2.10
MARGIN = 0.5
MIN_DURATION = 4.0


def load_detector():
    """Load and return the initialized AASIST-L anti-spoofing detector."""
    detector = AASIST_L()
    detector.load()
    return detector


def predict_score_and_duration(detector, wav_path: str):
    """Read WAV file, calculate duration, convert to mono 16kHz float32, and return score & duration."""
    audio, sr = sf.read(wav_path, dtype="float32")
    duration_seconds = len(audio) / float(sr)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    score = detector.score_batch([audio], [16000])[0]
    return score, duration_seconds


def main():
    print("=" * 60)
    print("VoiceGuard Live Audio Deepfake Classifier")
    print("=" * 60)

    # Determine input audio path from sys.argv or default fallback
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        # Default fallback test clip if no CLI argument provided
        default_path = os.path.join(BASE_DIR, "data", "fake", "fake_sample.wav")
        if os.path.exists(default_path):
            target_path = default_path
            print(f"No file path provided in args. Using default test file: {target_path}\n")
        else:
            print("Usage: python backend/notebooks/test_live_classify.py <path_to_audio.wav>")
            return

    if not os.path.exists(target_path):
        print(f"Error: Target file not found at '{target_path}'")
        sys.exit(1)

    print(f"Target Audio File: {target_path}")
    print(f"Loading AASIST-L detector from {MODEL_DIR}...")
    detector = load_detector()
    print("AASIST-L model loaded successfully.\n")

    print("Running inference...")
    score, duration = predict_score_and_duration(detector, target_path)

    # Classify score with minimum duration check
    res = classify_with_duration_check(
        score, RECOMMENDED_THRESHOLD, duration_seconds=duration, min_duration=MIN_DURATION, margin=MARGIN
    )

    # Print clear result line
    if res == "REAL":
        result_text = "RESULT: REAL"
    elif res == "FAKE":
        result_text = "RESULT: FAKE"
    elif res == "INCONCLUSIVE":
        result_text = "RESULT: INCONCLUSIVE (score too close to threshold)"
    else:
        result_text = f"RESULT: {res}"

    print("=" * 60)
    print(result_text)
    print(f"Score: {score:.2f} | Duration: {duration:.2f}s | Threshold: {RECOMMENDED_THRESHOLD:.2f} | Result: {res}")
    print("=" * 60)


if __name__ == "__main__":
    main()
