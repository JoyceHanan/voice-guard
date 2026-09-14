"""Threshold Optimization Script for VoiceGuard AASIST-L.

Sweeps threshold values across observed real/fake score ranges to find
the threshold maximizing classification accuracy and balancing FPR/FNR.
"""

import glob
import os

from pathlib import Path

import sys

import librosa
import numpy as np
import soundfile as sf

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "backend" / "models" / "aasist"
DATA_DIR = BASE_DIR / "data"
REAL_DIR = DATA_DIR / "real"
FAKE_DIR = DATA_DIR / "fake"

sys.path.insert(0, str(MODEL_DIR))
from aasist_l import AASIST_L


def load_detector():
  detector = AASIST_L()
  detector.load()
  return detector


def predict(detector, wav_path):
  audio, sr = sf.read(wav_path, dtype="float32")
  if audio.ndim > 1:
    audio = audio.mean(axis=1)
  if sr != 16000:
    audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
  return detector.score_batch([audio], [16000])[0]


def main():
  print("=" * 60)
  print("VoiceGuard Threshold Optimization")
  print("=" * 60)

  detector = load_detector()

  real_files = sorted(glob.glob(os.path.join(REAL_DIR, "*.wav")))
  fake_files = sorted(glob.glob(os.path.join(FAKE_DIR, "*.wav")))

  if not real_files or not fake_files:
    print("Error: Needs both real and fake samples in data/real and data/fake.")
    return

  print(
    f"Scoring {len(real_files)} real samples and {len(fake_files)} fake"
    " samples..."
  )
  real_scores = [predict(detector, f) for f in real_files]
  fake_scores = [predict(detector, f) for f in fake_files]

  min_s = min(min(real_scores), min(fake_scores))
  max_s = max(max(real_scores), max(fake_scores))

  print(
    f"Score Range: Min = {min_s:.4f}, Max = {max_s:.4f}. Sweeping threshold"
    " step = 0.10...\n"
  )

  # Sweep thresholds in steps of 0.1
  thresholds = np.arange(
      np.floor(min_s * 10) / 10, np.ceil(max_s * 10) / 10 + 0.1, 0.10
  )

  results = []
  total_samples = len(real_scores) + len(fake_scores)

  for t in thresholds:
    # Real predicted as real if score >= t
    tp = sum(1 for s in real_scores if s >= t)
    fn = sum(1 for s in real_scores if s < t)

    # Fake predicted as fake if score < t
    tn = sum(1 for s in fake_scores if s < t)
    fp = sum(1 for s in fake_scores if s >= t)

    acc = (tp + tn) / total_samples
    fpr = fp / len(fake_scores)
    fnr = fn / len(real_scores)

    results.append({
        "threshold": round(float(t), 2),
        "accuracy": acc,
        "fpr": fpr,
        "fnr": fnr,
        "diff_fp_fn": abs(fpr - fnr),
    })

  # Sort by accuracy descending, then balance of FPR/FNR ascending
  sorted_results = sorted(
      results, key=lambda x: (-x["accuracy"], x["diff_fp_fn"])
  )

  print(f"{'Rank':<6}{'Threshold':<12}{'Accuracy':<12}{'FPR':<10}{'FNR':<10}")
  print("-" * 50)
  for i, r in enumerate(sorted_results[:5], 1):
    print(
        f"{i:<6}{r['threshold']:<12.2f}{r['accuracy']*100:<11.2f}%{r['fpr']*100:<9.2f}%{r['fnr']*100:<9.2f}%"
    )

  best = sorted_results[0]
  print("\n" + "=" * 60)
  print(f"RECOMMENDED THRESHOLD: {best['threshold']:.2f}")
  print(
      f"Optimal Accuracy: {best['accuracy']*100:.2f}% | FPR: {best['fpr']*100:.2f}%"
      f" | FNR: {best['fnr']*100:.2f}%"
  )
  print("=" * 60)


if __name__ == "__main__":
  main()
