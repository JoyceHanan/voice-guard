from huggingface_hub import HfApi, hf_hub_download

api = HfApi()

print("Searching datasets containing 'hindi' or 'hi' with individual audio files...", flush=True)
hindi_query_results = list(api.list_datasets(search="hindi", limit=50))
for d in hindi_query_results:
    try:
        files = api.list_repo_files(repo_id=d.id, repo_type="dataset")
        audio_files = [f for f in files if f.lower().endswith(".wav") or f.lower().endswith(".mp3") or f.lower().endswith(".flac")]
        if len(audio_files) >= 40:
            print(f"FOUND FAST HINDI REPO: {d.id} with {len(audio_files)} audio files!", flush=True)
            print(f"  Sample: {audio_files[0]}", flush=True)
    except Exception as e:
        pass

print("\nSearching datasets containing 'telugu' with individual audio files...", flush=True)
telugu_query_results = list(api.list_datasets(search="telugu", limit=30))
for d in telugu_query_results:
    try:
        files = api.list_repo_files(repo_id=d.id, repo_type="dataset")
        audio_files = [f for f in files if f.lower().endswith(".wav") or f.lower().endswith(".mp3") or f.lower().endswith(".flac")]
        if len(audio_files) >= 40:
            print(f"FOUND FAST TELUGU REPO: {d.id} with {len(audio_files)} audio files!", flush=True)
            print(f"  Sample: {audio_files[0]}", flush=True)
    except Exception as e:
        pass
