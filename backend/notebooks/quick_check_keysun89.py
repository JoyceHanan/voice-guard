from huggingface_hub import HfApi

api = HfApi()

for repo in ["keysun89/hindi_data_975_line", "keysun89/hindi_data_975_original", "bnriiitb/telugu_asr"]:
    print(f"Listing {repo}...", flush=True)
    try:
        files = api.list_repo_files(repo_id=repo, repo_type="dataset")
        wavs = [f for f in files if f.lower().endswith(".wav") or f.lower().endswith(".mp3") or f.lower().endswith(".flac")]
        print(f"SUCCESS: {repo} has {len(wavs)} audio files!", flush=True)
        if wavs:
            print("  First 3:", wavs[:3], flush=True)
    except Exception as e:
        print(f"FAILED {repo}: {e}", flush=True)
