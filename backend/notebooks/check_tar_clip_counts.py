import tarfile
import os
import tempfile
import librosa

def count_tar_clips(tar_path, min_duration=4.0):
    if not os.path.exists(tar_path):
        return 0
    valid_count = 0
    total_files = 0
    with tempfile.TemporaryDirectory() as temp_dir:
        with tarfile.open(tar_path, "r") as tar:
            members = [m for m in tar.getmembers() if m.isfile() and m.name.endswith(('.mp3', '.wav', '.flac'))]
            total_files = len(members)
            for m in members:
                tar.extract(m, temp_dir)
                path = os.path.join(temp_dir, m.name)
                try:
                    dur = librosa.get_duration(path=path)
                    if dur >= min_duration:
                        valid_count += 1
                except Exception as e:
                    pass
    return valid_count, total_files

print("Checking scratch/hindi_dev.tar...")
hi_valid, hi_total = count_tar_clips("scratch/hindi_dev.tar")
print(f"Hindi dev tar: {hi_valid} valid (>=4s) out of {hi_total} total audio files")

print("\nChecking scratch/telugu_dev.tar...")
te_valid, te_total = count_tar_clips("scratch/telugu_dev.tar")
print(f"Telugu dev tar: {te_valid} valid (>=4s) out of {te_total} total audio files")
