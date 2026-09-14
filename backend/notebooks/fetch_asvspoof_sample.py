"""Fetch ASVspoof 2019 LA Test Sample Slice.

Fetches a small, random, reproducible slice (40 bonafide + 40 spoofed) from
SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA dataset on Hugging Face and saves them
as WAV files into data/real/ and data/fake/.
"""

import io
import os
import sys
from pathlib import Path
import numpy as np
import soundfile as sf
from datasets import load_dataset, Audio

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REAL_DIR = DATA_DIR / "real"
FAKE_DIR = DATA_DIR / "fake"

REAL_DIR.mkdir(parents=True, exist_ok=True)
FAKE_DIR.mkdir(parents=True, exist_ok=True)


def get_dir_size(path: Path) -> int:
    """Calculate total size of files in a directory in bytes."""
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def main():
    print("=" * 60)
    print("Fetching ASVspoof 2019 LA Test Sample Slice")
    print("=" * 60)

    size_before = get_dir_size(DATA_DIR)
    print(f"Data directory size BEFORE download: {size_before} bytes ({size_before / (1024 * 1024):.2f} MB)\n")

    print("Loading Hugging Face dataset: SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA (split='test', streaming=True)...")
    try:
        ds = load_dataset("SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA", split="test", streaming=True)
        ds = ds.cast_column("audio", Audio(decode=False))
    except Exception as e:
        print(f"\n[ERROR] Failed to access Hugging Face dataset: {e}")
        print("Stopping execution per safety constraints.")
        sys.exit(1)

    print(f"Dataset Features: {ds.features}")

    # Label inspection: ClassLabel(names=['bonafide', 'spoof'])
    # label 0 -> bonafide (real)
    # label 1 -> spoof (fake)
    label_feature = ds.features.get("label")
    if hasattr(label_feature, "names"):
        print(f"Label Mapping: 0 -> {label_feature.names[0]} (REAL), 1 -> {label_feature.names[1]} (FAKE)")
    else:
        print("Label Feature: 0 = bonafide (REAL), 1 = spoof (FAKE)")

    # Shuffle with fixed seed for reproducible selection
    shuffled_ds = ds.shuffle(seed=42, buffer_size=1000)

    target_count = 40
    real_saved = 0
    fake_saved = 0
    sample_rate_logged = None

    print(f"\nSelecting up to {target_count} real and {target_count} fake samples...")

    for item in shuffled_ds:
        if real_saved >= target_count and fake_saved >= target_count:
            break

        label = item["label"]
        audio_info = item["audio"]
        audio_bytes = audio_info["bytes"]

        # Decode audio using soundfile
        audio_data, sr = sf.read(io.BytesIO(audio_bytes))

        if sample_rate_logged is None:
            sample_rate_logged = sr
            print(f"Dataset Audio Sample Rate: {sr} Hz")

        if label == 0 and real_saved < target_count:
            real_saved += 1
            out_path = REAL_DIR / f"asvspoof_real_{real_saved:02d}.wav"
            sf.write(out_path, audio_data, sr, subtype="PCM_16")
        elif label == 1 and fake_saved < target_count:
            fake_saved += 1
            out_path = FAKE_DIR / f"asvspoof_fake_{fake_saved:02d}.wav"
            sf.write(out_path, audio_data, sr, subtype="PCM_16")

    size_after = get_dir_size(DATA_DIR)
    added_bytes = size_after - size_before

    print("\n" + "=" * 60)
    print("FETCH SUMMARY")
    print("=" * 60)
    print(f"Real (bonafide) files saved: {real_saved} -> {REAL_DIR}")
    print(f"Fake (spoofed) files saved:  {fake_saved} -> {FAKE_DIR}")
    print(f"Data folder size BEFORE: {size_before} bytes ({size_before / (1024 * 1024):.2f} MB)")
    print(f"Data folder size AFTER:  {size_after} bytes ({size_after / (1024 * 1024):.2f} MB)")
    print(f"Net added size:          {added_bytes} bytes ({added_bytes / (1024 * 1024):.2f} MB)")
    print("=" * 60)


if __name__ == "__main__":
    main()
