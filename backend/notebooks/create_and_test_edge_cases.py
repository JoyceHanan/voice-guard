"""Edge Case Degradation & Evaluation Script for VoiceGuard.

Generates degraded versions (added noise, 2s trim, 8kHz downsampling)
for clean real and fake reference samples, and evaluates classifier robust performance.
"""

import os
from pathlib import Path
import sys
import librosa
import numpy as np
import soundfile as sf

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "backend" / "models" / "aasist"
BACKEND_DIR = BASE_DIR / "backend"
EDGE_DIR = BASE_DIR / "data" / "edge_cases"
EDGE_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(MODEL_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from aasist_l import AASIST_L
from classifier import classify

RECOMMENDED_THRESHOLD = 2.10
MARGIN = 0.5


def load_detector():
    detector = AASIST_L()
    detector.load()
    return detector


def create_degradations(source_wav, prefix):
    audio, sr = sf.read(source_wav, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
        sr = 16000

    # Clean version
    clean_path = EDGE_DIR / f"{prefix}_clean.wav"
    sf.write(clean_path, audio, sr, subtype="PCM_16")

    # a) Added background white noise (std ~0.008)
    np.random.seed(42)
    noise = np.random.normal(0, 0.008, len(audio)).astype(np.float32)
    noisy_audio = np.clip(audio + noise, -1.0, 1.0)
    noisy_path = EDGE_DIR / f"{prefix}_noisy.wav"
    sf.write(noisy_path, noisy_audio, sr, subtype="PCM_16")

    # b) Trimmed to 2 seconds (32,000 samples at 16kHz)
    two_sec_audio = audio[:32000] if len(audio) >= 32000 else audio
    twosec_path = EDGE_DIR / f"{prefix}_2sec.wav"
    sf.write(twosec_path, two_sec_audio, sr, subtype="PCM_16")

    # c) Reduced to 8kHz sample rate (downsample 16k -> 8k -> 16k to simulate phone call quality)
    audio_8k = librosa.resample(audio, orig_sr=16000, target_sr=8000)
    audio_resampled = librosa.resample(audio_8k, orig_sr=8000, target_sr=16000)
    eightkhz_path = EDGE_DIR / f"{prefix}_8khz.wav"
    sf.write(eightkhz_path, audio_resampled, 16000, subtype="PCM_16")

    return {
        "clean": str(clean_path),
        "noisy": str(noisy_path),
        "2sec": str(twosec_path),
        "8khz": str(eightkhz_path),
    }


def predict_and_classify(detector, wav_path):
    audio, sr = sf.read(wav_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    score = detector.score_batch([audio], [16000])[0]
    label = classify(score, RECOMMENDED_THRESHOLD, margin=MARGIN)
    return score, label


def main():
    print("=" * 60)
    print("VoiceGuard Edge Case Degradation & Robustness Test")
    print("=" * 60)

    detector = load_detector()

    # Reference source files
    src_real = BASE_DIR / "data" / "real" / "asvspoof_real_01.wav"
    src_fake = BASE_DIR / "data" / "fake" / "asvspoof_fake_01.wav"

    real_degrads = create_degradations(src_real, "real")
    fake_degrads = create_degradations(src_fake, "fake")

    eval_items = [
        ("Real Sample", real_degrads),
        ("Fake Sample", fake_degrads),
    ]

    summary_table = []

    for category, degrads in eval_items:
        print(f"\nEvaluating {category}:")
        clean_score, clean_label = predict_and_classify(detector, degrads["clean"])
        print(f"  Clean reference : Score = {clean_score:6.2f} | Result = {clean_label}")

        for deg_type in ["noisy", "2sec", "8khz"]:
            score, label = predict_and_classify(detector, degrads[deg_type])
            changed = "CHANGED" if label != clean_label else "UNCHANGED"
            print(
                f"  Degraded ({deg_type:<5}): Score = {score:6.2f} | Result = {label:<12} | Status: {changed}"
            )
            summary_table.append({
                "category": category,
                "degradation": deg_type,
                "clean_label": clean_label,
                "score": score,
                "label": label,
                "changed": changed,
            })

    print("\n" + "=" * 60)
    print("EDGE CASE SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Sample':<14}{'Degradation':<14}{'Clean Result':<14}{'Score':<10}{'Degraded Result':<14}{'Status':<10}")
    print("-" * 76)
    for item in summary_table:
        print(
            f"{item['category']:<14}{item['degradation']:<14}{item['clean_label']:<14}{item['score']:<10.2f}{item['label']:<14}{item['changed']:<10}"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()
