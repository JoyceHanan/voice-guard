from huggingface_hub import HfApi, hf_hub_download

api = HfApi()

print("Listing files in fsicoli/common_voice_17_0...")
try:
    files = api.list_repo_files(repo_id="fsicoli/common_voice_17_0", repo_type="dataset")
    hi_files = [f for f in files if "audio/hi/" in f]
    te_files = [f for f in files if "audio/te/" in f]
    ta_files = [f for f in files if "audio/ta/" in f]
    kn_files = [f for f in files if "audio/kn/" in f]
    mr_files = [f for f in files if "audio/mr/" in f]
    
    print("Hindi (hi) files:", hi_files)
    print("Telugu (te) files:", te_files)
    print("Tamil (ta) files:", ta_files)
    print("Kannada (kn) files:", kn_files)
    print("Marathi (mr) files:", mr_files)
except Exception as e:
    print("Error:", e)
