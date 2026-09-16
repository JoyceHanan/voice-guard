"""Fetch 60 additional bonafide and 60 additional spoofed samples from ASVspoof 2019 LA test set (optimized streaming mode).
"""

import io
import os
from pathlib import Path
import sys
import soundfile as sf
from datasets import load_dataset, Audio

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REAL_DIR = DATA_DIR / "real"
FAKE_DIR = DATA_DIR / "fake"

REAL_DIR.mkdir(parents=True, exist_ok=True)
FAKE_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 60)
    print("Streaming 60 Additional Real and 60 Additional Fake ASVspoof Samples")
    print("=" * 60)

    print("Loading Hugging Face dataset: SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA (split='test', streaming=True)...")
    ds = load_dataset("SpeechAntiSpoofingBenchmarks/ASVspoof2019_LA", split="test", streaming=True)
    ds = ds.cast_column("audio", Audio(decode=False))

    target_count = 60
    real_saved = 0
    fake_saved = 0

    real_start_idx = 41
    fake_start_idx = 41

    skip_count = 100
    current_idx = 0

    print(f"Skipping first {skip_count} samples to guarantee non-overlapping fresh dataset slice...")

    for item in ds:
        current_idx += 1
        if current_idx <= skip_count:
            continue

        if real_saved >= target_count and fake_saved >= target_count:
            break

        label = item["label"]

        if label == 0 and real_saved < target_count:
            audio_info = item["audio"]
            audio_bytes = audio_info["bytes"]
            audio_data, sr = sf.read(io.BytesIO(audio_bytes))

            idx = real_start_idx + real_saved
            out_path = REAL_DIR / f"asvspoof_real_{idx:02d}.wav"
            sf.write(out_path, audio_data, sr, subtype="PCM_16")
            real_saved += 1
            print(f"[{real_saved + fake_saved}/120] Saved Real #{idx}: {out_path.name}")
        elif label == 1 and fake_saved < target_count:
            audio_info = item["audio"]
            audio_bytes = audio_info["bytes"]
            audio_data, sr = sf.read(io.BytesIO(audio_bytes))

            idx = fake_start_idx + fake_saved
            out_path = FAKE_DIR / f"asvspoof_fake_{idx:02d}.wav"
            sf.write(out_path, audio_data, sr, subtype="PCM_16")
            fake_saved += 1
            print(f"[{real_saved + fake_saved}/120] Saved Fake #{idx}: {out_path.name}")

    print("\n" + "=" * 60)
    print(f"FETCH COMPLETE: Saved {real_saved} real and {fake_saved} fake samples.")
    total_real = len(list(REAL_DIR.glob("*.wav")))
    total_fake = len(list(FAKE_DIR.glob("*.wav")))
    print(f"Total dataset size now: {total_real} real, {total_fake} fake (Total {total_real + total_fake} samples).")
    print("=" * 60)


if __name__ == "__main__":
    main()
