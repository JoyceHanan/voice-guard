from huggingface_hub import HfApi, hf_hub_download

api = HfApi()

print("Searching datasets with 'hindi' for wav files...")
datasets = list(api.list_datasets(search="hindi", limit=30))
for d in datasets:
    try:
        files = api.list_repo_files(repo_id=d.id, repo_type="dataset")
        wavs = [f for f in files if f.endswith(".wav") or f.endswith(".mp3") or f.endswith(".flac")]
        if len(wavs) >= 40:
            print(f"FOUND HINDI WAV REPO: {d.id} with {len(wavs)} audio files!")
            print("  Sample:", wavs[0])
    except Exception as e:
        pass

print("\nSearching datasets with 'telugu' for wav files...")
datasets_te = list(api.list_datasets(search="telugu", limit=30))
for d in datasets_te:
    try:
        files = api.list_repo_files(repo_id=d.id, repo_type="dataset")
        wavs = [f for f in files if f.endswith(".wav") or f.endswith(".mp3") or f.endswith(".flac")]
        if len(wavs) >= 40:
            print(f"FOUND TELUGU WAV REPO: {d.id} with {len(wavs)} audio files!")
            print("  Sample:", wavs[0])
    except Exception as e:
        pass
