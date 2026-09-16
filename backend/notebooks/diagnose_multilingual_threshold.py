"""Multilingual Threshold Calibration Diagnostic Script (Informational Only).

Calculates the hypothetical decision threshold that would best separate the real vs fake scores
for the 10 preliminary Hindi/Telugu samples.

IMPORTANT: This is a diagnostic exercise only for roadmap planning, NOT a deployed fix.
"""

import glob
import os
from pathlib import Path
import sys
import numpy as np
import soundfile as sf
import librosa

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BACKEND_DIR / "models" / "aasist"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(MODEL_DIR))

from aasist_l import AASIST_L

VALIDATED_ENGLISH_THRESHOLD = 2.10


def load_detector():
    detector = AASIST_L()
    detector.load()
    return detector


def predict(model, wav_path):
    audio, sr = sf.read(wav_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    return float(model.score_batch([audio], [16000])[0])


def main():
    print("=" * 80)
    print("VoiceGuard Multilingual Threshold Diagnostic (Informational / Roadmap Only)")
    print("=" * 80)

    detector = load_detector()

    multi_dir = BASE_DIR / "data" / "multilingual"
    fake_files = sorted(glob.glob(str(multi_dir / "fake" / "*.wav")))
    real_files = sorted(glob.glob(str(multi_dir / "real" / "*.wav")))

    real_scores = [predict(detector, f) for f in real_files]
    fake_scores = [predict(detector, f) for f in fake_files]

    print(f"\nReal Sample Scores ({len(real_scores)}):", [round(s, 4) for s in real_scores])
    print(f"Fake Sample Scores ({len(fake_scores)}):", [round(s, 4) for s in fake_scores])

    # Search candidates from min score to max score
    all_scores = real_scores + fake_scores
    min_s, max_s = min(all_scores), max(all_scores)
    candidates = np.arange(min_s - 0.5, max_s + 0.5, 0.05)

    best_thresh = None
    best_acc = -1.0
    best_tp = 0
    best_tn = 0

    for t in candidates:
        tp = sum(1 for s in real_scores if s >= t)
        tn = sum(1 for s in fake_scores if s < t)
        acc = (tp + tn) / len(all_scores)
        if acc > best_acc:
            best_acc = acc
            best_thresh = t
            best_tp = tp
            best_tn = tn

    print("\n" + "-" * 80)
    print("DIAGNOSTIC FINDING (NOT A DEPLOYED FIX):")
    print(f"- Validated English Baseline Threshold : {VALIDATED_ENGLISH_THRESHOLD:.2f}")
    print(f"- Hypothetical Multilingual Threshold : {best_thresh:.2f}")
    print(f"- Hypothetical Accuracy on 10 Samples  : {best_acc * 100:.2f}% ({best_tp + best_tn}/10)")
    print(f"  (Real Correct: {best_tp}/{len(real_scores)}, Fake Correct: {best_tn}/{len(fake_scores)})")
    print("-" * 80)

    print("\n[CRITICAL CAVEAT / ROADMAP NOTE]:")
    print("This threshold calculation is purely diagnostic to inform engineering roadmap discussions.")
    print("A threshold calibrated on a 10-sample set is NOT statistically reliable for production.")
    print("Deploying language-specific thresholds in production would require large-scale labeled datasets")
    print("and rigorous cross-validation. Fine-tuning a multilingual model (e.g. Wav2Vec2-XLSR-53)")
    print("remains the recommended architectural solution.")


if __name__ == "__main__":
    main()
