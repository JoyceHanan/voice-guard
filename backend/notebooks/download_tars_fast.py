import urllib.request
import os
import tarfile
import time

urls = {
    "hindi": "https://huggingface.co/datasets/fsicoli/common_voice_17_0/resolve/main/audio/hi/dev/hi_dev_0.tar",
    "telugu": "https://huggingface.co/datasets/fsicoli/common_voice_17_0/resolve/main/audio/te/dev/te_dev_0.tar"
}

os.makedirs("scratch", exist_ok=True)

for lang, url in urls.items():
    dest_path = f"scratch/{lang}_dev.tar"
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000000:
        print(f"{lang} tar already exists ({os.path.getsize(dest_path)/(1024*1024):.2f} MB)")
        continue
    print(f"Downloading {lang} tar from {url}...")
    t0 = time.time()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        block_size = 1024 * 512 # 512KB chunks
        while True:
            buffer = response.read(block_size)
            if not buffer:
                break
            downloaded += len(buffer)
            out_file.write(buffer)
            if total_size > 0:
                pct = (downloaded / total_size) * 100
                print(f"  {lang}: {downloaded/(1024*1024):.2f} MB / {total_size/(1024*1024):.2f} MB ({pct:.1f}%) in {time.time()-t0:.1f}s", flush=True)
            else:
                print(f"  {lang}: {downloaded/(1024*1024):.2f} MB in {time.time()-t0:.1f}s", flush=True)

print("Done downloading tars!")
