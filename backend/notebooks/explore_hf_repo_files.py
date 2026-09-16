from huggingface_hub import HfApi

api = HfApi()

repos = [
    "google/fleurs",
    "mozilla-foundation/common_voice_17_0",
    "mozilla-foundation/common_voice_13_0",
    "fsicoli/common_voice_17_0",
    "parambharat/telugu_asr_corpus",
    "bnriiitb/telugu_asr"
]

for repo_id in repos:
    print(f"=== {repo_id} ===")
    try:
        files = api.list_repo_files(repo_id=repo_id, repo_type="dataset")
        print(f"Found {len(files)} files. First 10:")
        for f in files[:10]:
            print("  ", f)
    except Exception as e:
        print("  Error:", e)
    print()
