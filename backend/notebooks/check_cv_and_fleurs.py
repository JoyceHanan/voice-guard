import os
import torch
from datasets import load_dataset, Audio

print("Checking Common Voice versions...")
cv_versions = ["mozilla-foundation/common_voice_17_0", "mozilla-foundation/common_voice_13_0", "mozilla-foundation/common_voice_11_0"]
languages = ["hi", "te", "ta", "kn", "mr"]

cv_results = {}
for ver in cv_versions:
    cv_results[ver] = {}
    for lang in languages:
        try:
            ds = load_dataset(ver, lang, split="train", streaming=True)
            ds = ds.cast_column("audio", Audio(decode=False))
            item = next(iter(ds))
            cv_results[ver][lang] = "AVAILABLE"
            print(f"[{ver}] [{lang}]: SUCCESS!")
        except Exception as e:
            cv_results[ver][lang] = f"FAILED ({str(e)[:60]})"
            print(f"[{ver}] [{lang}]: FAILED ({str(e)[:60]})")

print("\nChecking google/fleurs as alternative...")
fleurs_langs = ["hi_in", "te_in", "ta_in", "kn_in", "mr_in"]
for flang in fleurs_langs:
    try:
        ds = load_dataset("google/fleurs", flang, split="train", streaming=True)
        ds = ds.cast_column("audio", Audio(decode=False))
        item = next(iter(ds))
        print(f"[google/fleurs] [{flang}]: SUCCESS!")
    except Exception as e:
        print(f"[google/fleurs] [{flang}]: FAILED ({str(e)[:60]})")
