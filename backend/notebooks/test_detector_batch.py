import os
import glob
from pathlib import Path
import sys
import soundfile as sf
import librosa

MODEL_DIR = str(Path(__file__).resolve().parent.parent / "models" / "aasist")
DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")

REAL_DIR = os.path.join(DATA_DIR, "real")
FAKE_DIR = os.path.join(DATA_DIR, "fake")

sys.path.insert(0, MODEL_DIR)
from aasist_l import AASIST_L


def load_model(model_dir):
    detector = AASIST_L()
    detector.load()
    return detector


def predict(model, wav_path):
    audio, sr = sf.read(wav_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
    return model.score_batch([audio], [16000])[0]


def get_wav_files(folder):
    return sorted(glob.glob(os.path.join(folder, "*.wav")))


def main():
    print("=" * 60)
    print("VoiceGuard Batch Detector Test (AASIST-L)")
    print("=" * 60)

    model = load_model(MODEL_DIR)

    real_files = get_wav_files(REAL_DIR)
    fake_files = get_wav_files(FAKE_DIR)

    if not real_files and not fake_files:
        print(f"No .wav files found. Put real clips in {REAL_DIR} and fake clips in {FAKE_DIR}")
        return

    results = []

    print(f"\nFound {len(real_files)} real samples, {len(fake_files)} fake samples.\n")
    print(f"{'File':<40}{'Label':<8}{'Score':>10}")
    print("-" * 60)

    for f in real_files:
        score = predict(model, f)
        results.append(("real", score, f))
        print(f"{os.path.basename(f):<40}{'real':<8}{score:>10.4f}")

    for f in fake_files:
        score = predict(model, f)
        results.append(("fake", score, f))
        print(f"{os.path.basename(f):<40}{'fake':<8}{score:>10.4f}")

    real_scores = [s for label, s, _ in results if label == "real"]
    fake_scores = [s for label, s, _ in results if label == "fake"]

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if real_scores:
        print(
            f"Real  -> mean: {sum(real_scores)/len(real_scores):.4f}, "
            f"min: {min(real_scores):.4f}, max: {max(real_scores):.4f}"
        )
    if fake_scores:
        print(
            f"Fake  -> mean: {sum(fake_scores)/len(fake_scores):.4f}, "
            f"min: {min(fake_scores):.4f}, max: {max(fake_scores):.4f}"
        )

    if real_scores and fake_scores:
        # simple suggested threshold: midpoint between the two means
        suggested_threshold = (
            sum(real_scores) / len(real_scores) + sum(fake_scores) / len(fake_scores)
        ) / 2
        print(f"\nSuggested threshold (midpoint of means): {suggested_threshold:.4f}")

        if fake_scores and real_scores and max(fake_scores) > min(real_scores):
            print("WARNING: real and fake score ranges overlap — threshold will misclassify some samples.")
        else:
            print("Real and fake score ranges are cleanly separated at this sample size.")


if __name__ == "__main__":
    main()
