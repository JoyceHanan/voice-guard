from huggingface_hub import HfApi

api = HfApi()

repos = [
    "keysun89/hindi_data_975_line",
    "keysun89/hindi_data_975_original",
    "keysun89/hindi_data_975_word",
    "bnriiitb/telugu_asr",
    "parambharat/telugu_asr_corpus",
    "shivam/hindi_pib_processed"
]

for r in repos:
    try:
        files = api.list_repo_files(repo_id=r, repo_type="dataset")
        audio_files = [f for f in files if f.endswith(".wav") or f.endswith(".mp3") or f.endswith(".flac")]
        print(f"Repo: {r} -> total files: {len(files)}, audio files: {len(audio_files)}")
        if audio_files:
            print("  Sample audio:", audio_files[:3])
    except Exception as e:
        print(f"Repo: {r} -> Error: {e}")
