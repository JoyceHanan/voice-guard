"""VoiceGuard AASIST-L Anti-Spoofing Model Test Script.

Loads the AASIST-L model, evaluates fake and (if present) real audio
samples, and compares their bona-fide scores.
"""

import os
import sys
import numpy as np
import soundfile as sf

# Ensure AASIST-L model directory is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(BASE_DIR, "backend", "models", "aasist")
sys.path.insert(0, MODEL_DIR)

from aasist_l import AASIST_L


def load_audio(file_path: str, target_sr: int = 16000) -> np.ndarray:
    """Load audio file, convert to mono, and resample to 16kHz if needed."""
    audio, sr = sf.read(file_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != target_sr:
        import librosa

        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    return audio


def main():
    print("=" * 60)
    print("VoiceGuard Anti-Spoofing Model Test (AASIST-L)")
    print("=" * 60)

    # 1. Load AASIST-L model
    print(f"Loading AASIST-L model from {MODEL_DIR}...")
    detector = AASIST_L()
    detector.load()
    print("AASIST-L model loaded successfully.\n")

    fake_path = os.path.join(BASE_DIR, "data", "fake_sample.wav")
    real_path = os.path.join(BASE_DIR, "data", "real_sample.wav")

    scores = {}

    # 2. Run inference on fake_sample.wav
    if os.path.exists(fake_path):
        print(f"Processing fake sample: {fake_path}")
        fake_audio = load_audio(fake_path)
        fake_score = detector.score_batch([fake_audio], [16000])[0]
        scores["fake"] = fake_score
        print(f"-> Fake Sample Score (bona-fide logit): {fake_score:.4f}")
    else:
        print(f"WARNING: {fake_path} not found!")

    # 3. Run inference on real_sample.wav if it exists
    if os.path.exists(real_path):
        print(f"\nProcessing real sample: {real_path}")
        real_audio = load_audio(real_path)
        real_score = detector.score_batch([real_audio], [16000])[0]
        scores["real"] = real_score
        print(f"-> Real Sample Score (bona-fide logit): {real_score:.4f}")
    else:
        print(f"\n[Note] '{real_path}' does not exist yet. Skipping real sample evaluation.")

    # 4. Compare scores and print clear final line
    print("\n" + "=" * 60)
    if "fake" in scores and "real" in scores:
        diff = abs(scores["real"] - scores["fake"])
        # AASIST-L: Higher score = more bona fide (real), Lower score = spoof (fake)
        if diff >= 1.0:
            print(
                f"SUCCESS: Real score ({scores['real']:.4f}) and Fake score ({scores['fake']:.4f}) "
                f"are meaningfully different (delta = {diff:.4f})."
            )
        else:
            print(
                f"NEUTRAL: Real score ({scores['real']:.4f}) and Fake score ({scores['fake']:.4f}) "
                f"have a small score difference (delta = {diff:.4f})."
            )
    elif "fake" in scores:
        print(
            f"RESULT: Evaluated fake sample score: {scores['fake']:.4f}. "
            "Add 'data/real_sample.wav' to compare real vs fake scores."
        )
    else:
        print("ERROR: No sample files found for evaluation.")
    print("=" * 60)


if __name__ == "__main__":
    main()
