import urllib.request
import os
import time

url_te_train = "https://huggingface.co/datasets/fsicoli/common_voice_17_0/resolve/main/audio/te/train/te_train_0.tar"
dest_path = "scratch/telugu_train.tar"

if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000000:
    print(f"Telugu train tar already exists ({os.path.getsize(dest_path)/(1024*1024):.2f} MB)")
else:
    print(f"Downloading Telugu train tar from {url_te_train}...")
    t0 = time.time()
    req = urllib.request.Request(url_te_train, headers={'User-Agent': 'Mozilla/5.0'})
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
                print(f"  telugu_train: {downloaded/(1024*1024):.2f} MB / {total_size/(1024*1024):.2f} MB ({pct:.1f}%) in {time.time()-t0:.1f}s", flush=True)

print("Finished checking/downloading Telugu train tar!")
