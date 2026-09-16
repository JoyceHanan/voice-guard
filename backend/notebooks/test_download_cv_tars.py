import tarfile
from huggingface_hub import hf_hub_download

print("Downloading fsicoli/common_voice_17_0 audio/hi/dev/hi_dev_0.tar...")
hi_path = hf_hub_download(repo_id="fsicoli/common_voice_17_0", filename="audio/hi/dev/hi_dev_0.tar", repo_type="dataset")
print("Hindi tar downloaded to:", hi_path)

with tarfile.open(hi_path, "r") as tar:
    members = tar.getmembers()
    print(f"Hindi dev tar contains {len(members)} items")
    for m in members[:5]:
        print(" ", m.name, m.size)

print("\nDownloading fsicoli/common_voice_17_0 audio/te/dev/te_dev_0.tar...")
te_path = hf_hub_download(repo_id="fsicoli/common_voice_17_0", filename="audio/te/dev/te_dev_0.tar", repo_type="dataset")
print("Telugu tar downloaded to:", te_path)

with tarfile.open(te_path, "r") as tar:
    members = tar.getmembers()
    print(f"Telugu dev tar contains {len(members)} items")
    for m in members[:5]:
        print(" ", m.name, m.size)
