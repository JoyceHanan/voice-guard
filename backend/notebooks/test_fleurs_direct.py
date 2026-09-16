import os
import time
import soundfile as sf
import librosa
from datasets import load_dataset, Audio

print("Loading google/fleurs hi_in...")
t0 = time.time()
try:
    ds_hi = load_dataset("google/fleurs", "hi_in", split="train", streaming=True)
    print(f"Dataset object created in {time.time()-t0:.2f}s")
    count = 0
    for i, item in enumerate(ds_hi):
        audio_info = item["audio"]
        arr = audio_info["array"]
        sr = audio_info["sampling_rate"]
        dur = len(arr) / sr
        print(f"Sample {i}: sr={sr}, dur={dur:.2f}s, path={audio_info.get('path')}")
        count += 1
        if count >= 3:
            break
    print(f"Successfully iterated 3 samples in {time.time()-t0:.2f}s")
except Exception as e:
    print("FLEURS hi_in error:", e)

print("\nLoading google/fleurs te_in...")
t0 = time.time()
try:
    ds_te = load_dataset("google/fleurs", "te_in", split="train", streaming=True)
    print(f"Dataset object created in {time.time()-t0:.2f}s")
    count = 0
    for i, item in enumerate(ds_te):
        audio_info = item["audio"]
        arr = audio_info["array"]
        sr = audio_info["sampling_rate"]
        dur = len(arr) / sr
        print(f"Sample {i}: sr={sr}, dur={dur:.2f}s, path={audio_info.get('path')}")
        count += 1
        if count >= 3:
            break
    print(f"Successfully iterated 3 samples in {time.time()-t0:.2f}s")
except Exception as e:
    print("FLEURS te_in error:", e)
