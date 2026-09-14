"""Speaker Embedding Consistency Validation Script (Extended Diagnostics).

Evaluates L2-normalized ECAPA-TDNN speaker embeddings across 4 same-speaker
pairs and 4 different-speaker pairs to establish decision boundaries.
"""

import os
from pathlib import Path
import sys
import soundfile as sf

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "backend" / "models"
DATA_DIR = BASE_DIR / "data"

sys.path.insert(0, str(MODELS_DIR))
from speaker_embed import compute_cosine_similarity


def create_split_clips_for_same_speaker(source_wav: Path, prefix: str):
    """Split a WAV file into two halves."""
    audio, sr = sf.read(source_wav)
    mid = len(audio) // 2
    part1_path = DATA_DIR / f"{prefix}_part1.wav"
    part2_path = DATA_DIR / f"{prefix}_part2.wav"
    sf.write(part1_path, audio[:mid], sr)
    sf.write(part2_path, audio[mid:], sr)
    return str(part1_path), str(part2_path)


def main():
    print("=" * 80)
    print("VoiceGuard Speaker Embedding Consistency Diagnostics (L2-Normalized)")
    print("=" * 80)

    # Same speaker files (TTS voice model & Real split)
    fake0 = str(DATA_DIR / "fake" / "fake_sample.wav")
    fake1 = str(DATA_DIR / "holdout_fresh" / "fake" / "fresh_fake_01.wav")
    fake2 = str(DATA_DIR / "holdout_fresh" / "fake" / "fresh_fake_02.wav")
    fake3 = str(DATA_DIR / "holdout_fresh" / "fake" / "fresh_fake_03.wav")

    real1 = str(DATA_DIR / "real" / "asvspoof_real_01.wav")
    real2 = str(DATA_DIR / "real" / "asvspoof_real_02.wav")
    real3 = str(DATA_DIR / "real" / "asvspoof_real_03.wav")
    real4 = str(DATA_DIR / "real" / "asvspoof_real_04.wav")
    real5 = str(DATA_DIR / "real" / "asvspoof_real_05.wav")
    real6 = str(DATA_DIR / "real" / "asvspoof_real_06.wav")
    real7 = str(DATA_DIR / "real" / "asvspoof_real_07.wav")
    real8 = str(DATA_DIR / "real" / "asvspoof_real_08.wav")

    real1_parta, real1_partb = create_split_clips_for_same_speaker(
        DATA_DIR / "real" / "asvspoof_real_01.wav", "diag_same"
    )

    same_pairs = [
        ("Same Speaker 1 (TTS fake_sample vs fresh_fake_01)", fake0, fake1),
        ("Same Speaker 2 (TTS fresh_fake_01 vs fresh_fake_02)", fake1, fake2),
        ("Same Speaker 3 (TTS fresh_fake_02 vs fresh_fake_03)", fake2, fake3),
        ("Same Speaker 4 (ASVspoof Real 01 Part A vs Part B)", real1_parta, real1_partb),
    ]

    diff_pairs = [
        ("Diff Speaker 1 (ASVspoof Real 01 vs Real 02)", real1, real2),
        ("Diff Speaker 2 (ASVspoof Real 03 vs Real 04)", real3, real4),
        ("Diff Speaker 3 (ASVspoof Real 05 vs Real 06)", real5, real6),
        ("Diff Speaker 4 (ASVspoof Real 07 vs Real 08)", real7, real8),
    ]

    print(f"{'Pair Category & Description':<58}{'Similarity':>15}")
    print("-" * 80)

    same_scores = []
    print("--- SAME SPEAKER PAIRS ---")
    for desc, f1, f2 in same_pairs:
        sim = compute_cosine_similarity(f1, f2)
        same_scores.append(sim)
        print(f"{desc:<58}{sim:>15.4f}")

    diff_scores = []
    print("\n--- DIFFERENT SPEAKER PAIRS ---")
    for desc, f1, f2 in diff_pairs:
        sim = compute_cosine_similarity(f1, f2)
        diff_scores.append(sim)
        print(f"{desc:<58}{sim:>15.4f}")

    avg_same = sum(same_scores) / len(same_scores)
    avg_diff = sum(diff_scores) / len(diff_scores)
    margin_gap = avg_same - avg_diff

    print("\n" + "=" * 80)
    print("VERDICT & SUMMARY")
    print("=" * 80)
    print(f"Same-Speaker Similarity Mean:      {avg_same:.4f}  (Min: {min(same_scores):.4f}, Max: {max(same_scores):.4f})")
    print(f"Different-Speaker Similarity Mean: {avg_diff:.4f}  (Min: {min(diff_scores):.4f}, Max: {max(diff_scores):.4f})")
    print(f"Mean Similarity Separation Gap:    {margin_gap:.4f}")

    if avg_same >= 0.50 and margin_gap >= 0.30:
        print("\nVERDICT: CONFIRMED. Same-speaker similarity is consistently and meaningfully higher (gap >= 0.30).")
    else:
        print("\nVERDICT: INSUFFICIENT SEPARATION.")
    print("=" * 80)


if __name__ == "__main__":
    main()
