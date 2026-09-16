import tarfile
import os
import io
import soundfile as sf
import librosa
from huggingface_hub import hf_hub_download

print("Downloading FLEURS hi_in dev.tar.gz...")
try:
    path_hi = hf_hub_download(repo_id="google/fleurs", filename="data/hi_in/audio/dev.tar.gz", repo_type="dataset")
    print("Downloaded hi_in dev.tar.gz to:", path_hi)
    with tarfile.open(path_hi, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.name.endswith(".wav")]
        print(f"Found {len(members)} wav files in hi_in dev.tar.gz")
except Exception as e:
    print("FLEURS hi_in download error:", e)

print("\nDownloading FLEURS te_in dev.tar.gz...")
try:
    path_te = hf_hub_download(repo_id="google/fleurs", filename="data/te_in/audio/dev.tar.gz", repo_type="dataset")
    print("Downloaded te_in dev.tar.gz to:", path_te)
    with tarfile.open(path_te, "r:gz") as tar:
        members = [m for m in tar.getmembers() if m.name.endswith(".wav")]
        print(f"Found {len(members)} wav files in te_in dev.tar.gz")
except Exception as e:
    print("FLEURS te_in download error:", e)
