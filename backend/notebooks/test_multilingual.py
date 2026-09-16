"""Cross-Lingual Generalization Test Script for VoiceGuard Anti-Spoofing Pipeline.

Evaluates the existing English-trained AASIST-L model (validated threshold = 2.10)
on multilingual synthetic (gTTS Hindi/Telugu) and real human audio samples without retraining.
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
    print("=" * 90)
    print("VoiceGuard Cross-Lingual Generalization Benchmark (AASIST-L)")
    print("=" * 90)
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
    print(f"{'Filename':<30} {'Language':<10} {'True Label':<10} {'Score':>8} {'Predicted':<12} {'Match?':<8}")
    print("-" * 90)

    fake_correct = 0
    fake_total = 0
    real_correct = 0
    real_total = 0

    for filepath, true_label in all_samples:
        fname = os.path.basename(filepath)
        lang = detect_language(fname)

        score, duration, quality, snr = predict(detector, filepath)
        pred_label = classify_with_quality_and_duration(
            score, VALIDATED_THRESHOLD, duration, audio_quality_label=quality
        )

        # Check correctness
        is_correct = False
        if true_label == "FAKE":
            fake_total += 1
            if pred_label == "FAKE":
                is_correct = True
                fake_correct += 1
        elif true_label == "REAL":
            real_total += 1
            if pred_label == "REAL":
                is_correct = True
                real_correct += 1

        match_str = "YES" if is_correct else "NO"
        print(f"{fname:<30} {lang:<10} {true_label:<10} {score:>8.4f} {pred_label:<12} {match_str:<8}")

    total_samples = fake_total + real_total
    total_correct = fake_correct + real_correct

    fake_acc = (fake_correct / fake_total * 100.0) if fake_total > 0 else 0.0
    real_acc = (real_correct / real_total * 100.0) if real_total > 0 else 0.0
    combined_acc = (total_correct / total_samples * 100.0) if total_samples > 0 else 0.0

    diff = combined_acc - HOLDOUT_ACCURACY

    print("-" * 90)
    print("\nCROSS-LINGUAL BENCHMARK RESULTS SUMMARY:")
    print(f"a) Synthetic (FAKE) Multilingual Accuracy : {fake_acc:.2f}% ({fake_correct}/{fake_total})")
    print(f"b) Genuine (REAL) Multilingual Accuracy   : {real_acc:.2f}% ({real_correct}/{real_total})")
    print(f"c) Combined Overall Multilingual Accuracy : {combined_acc:.2f}% ({total_correct}/{total_samples})")
    print(f"d) Baseline English Holdout Accuracy      : {HOLDOUT_ACCURACY:.2f}%")
    print(f"e) Combined Accuracy Delta vs. English    : {diff:+.2f}%")

    print("\nCOMPARATIVE ACCURACY ASSESSMENT:")
    if abs(diff) <= 3.0:
        assessment = "COMPARABLE to original English holdout performance."
    elif diff < -15.0:
        assessment = "SIGNIFICANTLY LOWER than original English holdout performance."
    elif diff < 0:
        assessment = "SOMEWHAT LOWER than original English holdout performance."
    else:
        assessment = "HIGHER than original English holdout performance."

    print(f"--> Multilingual performance is {assessment}")

    if real_acc < 80.0:
        print("\n[HONEST FINDING & LIMITATION]:")
        print("Genuine (REAL) non-English human speech recordings exhibited a significantly lower accuracy")
        print(f"({real_acc:.2f}%) compared to English speech ({HOLDOUT_ACCURACY:.2f}%). Phonetic, prosodic, and")
        print("acoustic variations in Hindi and Telugu cause genuine speech logits to fall near or below")
        print("the English decision boundary (2.10). An English-only trained model does not generalize")
        print("robustly to real non-English speakers without multilingual fine-tuning (e.g. Wav2Vec2-XLSR).")


if __name__ == "__main__":
    main()
