"""Cross-Lingual Generalization Test Script for VoiceGuard Anti-Spoofing Pipeline.

Evaluates the existing English-trained AASIST-L model (validated threshold = 2.10)
on multilingual synthetic (gTTS Hindi/Telugu) and real audio samples without retraining.
"""

import glob
import os
from pathlib import Path
import sys
import soundfile as sf
import librosa

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BACKEND_DIR / "models" / "aasist"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(MODEL_DIR))

from aasist_l import AASIST_L
from classifier import classify_with_quality_and_duration
from audio_quality import estimate_quality

VALIDATED_THRESHOLD = 2.10
HOLDOUT_ACCURACY = 94.44  # Baseline accuracy on English/ASVspoof dataset


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
    
    score = model.score_batch([audio], [16000])[0]
    duration = len(audio) / 16000.0
    quality_label, snr_db = estimate_quality(audio, 16000)
    return float(score), float(duration), quality_label, snr_db


def detect_language(filename: str) -> str:
    fname = filename.lower()
    if "hindi" in fname:
        return "Hindi"
    elif "telugu" in fname:
        return "Telugu"
    elif "english" in fname:
        return "English"
    return "Unknown"


def main():
    print("=" * 85)
    print("VoiceGuard Cross-Lingual Generalization Benchmark (AASIST-L)")
    print("=" * 85)
    print(f"Validated Decision Threshold: {VALIDATED_THRESHOLD:.2f}")
    print(f"Baseline English Holdout Accuracy: {HOLDOUT_ACCURACY:.2f}%\n")

    detector = load_detector()

    multi_dir = BASE_DIR / "data" / "multilingual"
    fake_dir = multi_dir / "fake"
    real_dir = multi_dir / "real"

    fake_files = sorted(glob.glob(str(fake_dir / "*.wav")))
    real_files = sorted(glob.glob(str(real_dir / "*.wav")))

    all_samples = []
    for f in fake_files:
        all_samples.append((f, "FAKE"))
    for f in real_files:
        all_samples.append((f, "REAL"))

    if not all_samples:
        print(f"No audio files found in {multi_dir}")
        return

    print(f"Found {len(fake_files)} synthetic (FAKE) samples and {len(real_files)} genuine (REAL) samples.\n")
    print(f"{'Filename':<25} {'Language':<10} {'True Label':<10} {'Score':>8} {'Predicted':<12} {'Match?':<8}")
    print("-" * 85)

    correct_count = 0
    total_evaluable = 0

    for filepath, true_label in all_samples:
        fname = os.path.basename(filepath)
        lang = detect_language(fname)

        score, duration, quality, snr = predict(detector, filepath)
        pred_label = classify_with_quality_and_duration(
            score, VALIDATED_THRESHOLD, duration, audio_quality_label=quality
        )

        # Check correctness
        is_correct = False
        if true_label == "FAKE" and pred_label == "FAKE":
            is_correct = True
        elif true_label == "REAL" and pred_label == "REAL":
            is_correct = True

        if is_correct:
            correct_count += 1
            match_str = "YES"
        else:
            match_str = "NO"

        total_evaluable += 1

        print(f"{fname:<25} {lang:<10} {true_label:<10} {score:>8.4f} {pred_label:<12} {match_str:<8}")

    multilingual_accuracy = (correct_count / total_evaluable * 100.0) if total_evaluable > 0 else 0.0

    print("-" * 85)
    print("\nCROSS-LINGUAL SUMMARY & COMPARISON:")
    print(f"- Total Multilingual Samples Tested: {total_evaluable}")
    print(f"- Correct Predictions: {correct_count} / {total_evaluable}")
    print(f"- Multilingual Dataset Accuracy: {multilingual_accuracy:.2f}%")
    print(f"- Baseline English Holdout Accuracy: {HOLDOUT_ACCURACY:.2f}%")
    diff = multilingual_accuracy - HOLDOUT_ACCURACY
    print(f"- Accuracy Delta: {diff:+.2f}%")

    if multilingual_accuracy < HOLDOUT_ACCURACY:
        print("\n[OBSERVATION]: Accuracy on non-English audio is lower than the English baseline.")
        print("This indicates that phonetic, acoustic, or prosodic shifts in non-English speech can affect")
        print("the model's confidence boundary when using an English-trained detector without fine-tuning.")
    elif multilingual_accuracy == 100.0:
        print("\n[OBSERVATION]: 100% accuracy achieved on current synthetic multilingual sample set.")
        print("Note: All tested samples were gTTS synthetic clips. Performance on real non-English speech")
        print("needs verification once genuine user recordings are added to data/multilingual/real/.")


if __name__ == "__main__":
    main()
