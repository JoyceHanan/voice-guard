"""VoiceGuard Calibration vs Holdout Validation Script.

Splits existing dataset into 80% calibration set and 20% holdout set,
computes optimal threshold on calibration set only, and evaluates
generalization on the holdout set.
"""

import glob
import os
from pathlib import Path
import random
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


def find_best_threshold(real_scores, fake_scores):
  min_s = min(min(real_scores), min(fake_scores))
  max_s = max(max(real_scores), max(fake_scores))

  thresholds = np.arange(
      np.floor(min_s * 10) / 10, np.ceil(max_s * 10) / 10 + 0.1, 0.10
  )

  results = []
  total_samples = len(real_scores) + len(fake_scores)

  for t in thresholds:
    tp = sum(1 for s in real_scores if s >= t)
    fn = sum(1 for s in real_scores if s < t)
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

  sorted_results = sorted(
      results, key=lambda x: (-x["accuracy"], x["diff_fp_fn"])
  )
  return sorted_results[0]


def evaluate_threshold(threshold, real_scores, fake_scores):
  tp = sum(1 for s in real_scores if s >= threshold)
  fn = sum(1 for s in real_scores if s < threshold)
  tn = sum(1 for s in fake_scores if s < threshold)
  fp = sum(1 for s in fake_scores if s >= threshold)

  total = len(real_scores) + len(fake_scores)
  acc = (tp + tn) / total if total > 0 else 0.0
  fpr = fp / len(fake_scores) if len(fake_scores) > 0 else 0.0
  fnr = fn / len(real_scores) if len(real_scores) > 0 else 0.0

  return {"accuracy": acc, "fpr": fpr, "fnr": fnr, "tp": tp, "tn": tn, "fp": fp, "fn": fn}


def main():
  print("=" * 60)
  print("VoiceGuard Train/Holdout Validation (80/20 Split)")
  print("=" * 60)

  detector = load_detector()

  real_files = sorted(glob.glob(os.path.join(REAL_DIR, "*.wav")))
  fake_files = sorted(glob.glob(os.path.join(FAKE_DIR, "*.wav")))

  # Reproducible 80/20 split with fixed random seed 42
  rng = random.Random(42)
  rng.shuffle(real_files)
  rng.shuffle(fake_files)

  n_real_calib = int(len(real_files) * 0.8)
  n_fake_calib = int(len(fake_files) * 0.8)

  calib_real_files = real_files[:n_real_calib]
  holdout_real_files = real_files[n_real_calib:]

  calib_fake_files = fake_files[:n_fake_calib]
  holdout_fake_files = fake_files[n_fake_calib:]

  print(f"Total Real Samples: {len(real_files)} -> Calib: {len(calib_real_files)}, Holdout: {len(holdout_real_files)}")
  print(f"Total Fake Samples: {len(fake_files)} -> Calib: {len(calib_fake_files)}, Holdout: {len(holdout_fake_files)}\n")

  # Predict scores
  print("Scoring calibration samples...")
  calib_real_scores = [predict(detector, f) for f in calib_real_files]
  calib_fake_scores = [predict(detector, f) for f in calib_fake_files]

  print("Scoring holdout samples...\n")
  holdout_real_scores = [predict(detector, f) for f in holdout_real_files]
  holdout_fake_scores = [predict(detector, f) for f in holdout_fake_files]

  # 1. Recalculate threshold on calibration set ONLY
  best_calib = find_best_threshold(calib_real_scores, calib_fake_scores)
  opt_threshold = best_calib["threshold"]

  # 2. Evaluate on holdout set
  holdout_eval = evaluate_threshold(opt_threshold, holdout_real_scores, holdout_fake_scores)

  print("=" * 60)
  print(f"OPTIMAL CALIBRATED THRESHOLD: {opt_threshold:.2f}")
  print("=" * 60)
  print(f"Calibration set accuracy: {best_calib['accuracy']*100:.2f}%  (FPR: {best_calib['fpr']*100:.2f}%, FNR: {best_calib['fnr']*100:.2f}%)")
  print(f"Holdout set accuracy:     {holdout_eval['accuracy']*100:.2f}%  (FPR: {holdout_eval['fpr']*100:.2f}%, FNR: {holdout_eval['fnr']*100:.2f}%)")
  print("=" * 60)


if __name__ == "__main__":
  main()
