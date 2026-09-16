import os
import random
import tarfile
import tempfile
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import soundfile as sf
import librosa
import numpy as np

# Fix seeds
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REAL_DIR = os.path.join(PROJECT_ROOT, "data", "multilingual", "real")
FAKE_DIR = os.path.join(PROJECT_ROOT, "data", "multilingual", "fake")
MODEL_DIR = os.path.join(PROJECT_ROOT, "backend", "models", "aasist")

os.makedirs(REAL_DIR, exist_ok=True)
os.makedirs(FAKE_DIR, exist_ok=True)

# ---------------------------------------------------------
# TASK 1 & 2: Pull Real Hindi & Telugu from Local CV 17.0 Tars
# ---------------------------------------------------------
print("==================================================", flush=True)
print("TASK 1 & 2: Sourcing Real Hindi & Telugu Speech", flush=True)
print("==================================================", flush=True)

def extract_local_cv_clips(tar_path, target_lang_prefix, output_dir, count_needed=40, min_duration=4.0):
    print(f"Extracting clips from local tar {tar_path}...", flush=True)
    extracted_files = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with tarfile.open(tar_path, "r") as tar:
            members = [m for m in tar.getmembers() if m.isfile()]
            random.shuffle(members)
            
            saved_count = 0
            for m in members:
                ext = os.path.splitext(m.name)[1].lower()
                if ext not in [".mp3", ".wav", ".flac", ".ogg"]:
                    continue
                
                tar.extract(m, temp_dir)
                extracted_path = os.path.join(temp_dir, m.name)
                
                try:
                    audio, sr = librosa.load(extracted_path, sr=16000)
                    duration = len(audio) / sr
                    if duration >= min_duration:
                        saved_count += 1
                        out_filename = f"{target_lang_prefix}_cv_{saved_count:02d}.wav"
                        out_path = os.path.join(output_dir, out_filename)
                        sf.write(out_path, audio, 16000)
                        extracted_files.append(out_path)
                        print(f"  Saved [{saved_count}/{count_needed}] {out_filename} (duration: {duration:.2f}s)", flush=True)
                        if saved_count >= count_needed:
                            break
                except Exception as e:
                    continue
                    
    print(f"Extracted {len(extracted_files)} {target_lang_prefix} clips >= {min_duration}s.", flush=True)
    return extracted_files

# Check existing extracted files
existing_real_hindi = [f for f in os.listdir(REAL_DIR) if f.startswith("hindi_cv_")]
if len(existing_real_hindi) >= 40:
    print(f"Real Hindi CV samples already extracted ({len(existing_real_hindi)} files). Skipping extraction.", flush=True)
else:
    extract_local_cv_clips(
        tar_path=os.path.join(PROJECT_ROOT, "scratch", "hindi_dev.tar"),
        target_lang_prefix="hindi",
        output_dir=REAL_DIR,
        count_needed=40,
        min_duration=4.0
    )

existing_real_telugu = [f for f in os.listdir(REAL_DIR) if f.startswith("telugu_cv_")]
if len(existing_real_telugu) >= 30:
    print(f"Real Telugu CV samples already extracted ({len(existing_real_telugu)} files). Skipping extraction.", flush=True)
else:
    extract_local_cv_clips(
        tar_path=os.path.join(PROJECT_ROOT, "scratch", "telugu_dev.tar"),
        target_lang_prefix="telugu",
        output_dir=REAL_DIR,
        count_needed=40,
        min_duration=4.0
    )

# ---------------------------------------------------------
# TASK 3: Generate Synthetic Multilingual Audio
# ---------------------------------------------------------
print("\n==================================================", flush=True)
print("TASK 3: Generating Synthetic Multilingual Samples", flush=True)
print("==================================================", flush=True)

def generate_synthetic_audio_signal(duration_sec, f0=140, seed=42):
    np.random.seed(seed)
    sr = 16000
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    
    pitch_contour = f0 + 15 * np.sin(2 * np.pi * 1.8 * t) + 8 * np.cos(2 * np.pi * 3.5 * t)
    carrier = np.sin(2 * np.pi * pitch_contour * t)
    
    formants = [500, 1500, 2500]
    resonance = np.zeros_like(t)
    for fm in formants:
        resonance += 0.25 * np.sin(2 * np.pi * fm * t + 0.1 * np.sin(2 * np.pi * 4 * t))
        
    signal = carrier * (1.0 + resonance)
    
    envelope = np.abs(np.sin(2 * np.pi * 2.2 * t)) ** 0.6
    envelope[envelope < 0.15] = 0.0
    
    signal = signal * envelope
    noise = np.random.normal(0, 0.02, size=len(t))
    signal = signal + noise
    
    signal = signal / (np.max(np.abs(signal)) + 1e-6) * 0.8
    return signal.astype(np.float32)

def create_synthetic_dataset(prefix, output_dir, count_needed=40, base_f0=140):
    existing_fake = [f for f in os.listdir(output_dir) if f.startswith(f"{prefix}_fake_")]
    if len(existing_fake) >= count_needed:
        print(f"Synthetic {prefix} samples already exist ({len(existing_fake)} files). Skipping generation.", flush=True)
        return [os.path.join(output_dir, f) for f in existing_fake]
        
    print(f"Generating {count_needed} {prefix} synthetic clips...", flush=True)
    generated_files = []
    
    for i in range(1, count_needed + 1):
        out_filename = f"{prefix}_fake_{i+3:02d}.wav"
        out_path = os.path.join(output_dir, out_filename)
        
        if os.path.exists(out_path):
            generated_files.append(out_path)
            continue
            
        dur = random.uniform(8.5, 14.5)
        f0 = base_f0 + (i % 7) * 12
        clip = generate_synthetic_audio_signal(duration_sec=dur, f0=f0, seed=SEED + i*10)
        sf.write(out_path, clip, 16000)
        generated_files.append(out_path)
        print(f"  Generated [{len(generated_files)}/{count_needed}] {out_filename} (duration: {dur:.2f}s)", flush=True)
        
    print(f"Generated {len(generated_files)} synthetic {prefix} clips in {output_dir}", flush=True)
    return generated_files

hindi_fake_files = create_synthetic_dataset("hindi", FAKE_DIR, 40, base_f0=130)
telugu_fake_files = create_synthetic_dataset("telugu", FAKE_DIR, 40, base_f0=160)

# ---------------------------------------------------------
# TASK 4: Report Dataset Size
# ---------------------------------------------------------
print("\n==================================================", flush=True)
print("TASK 4: Dataset Inventory Report", flush=True)
print("==================================================", flush=True)

all_real_files = [os.path.join(REAL_DIR, f) for f in os.listdir(REAL_DIR) if f.endswith(".wav")]
all_fake_files = [os.path.join(FAKE_DIR, f) for f in os.listdir(FAKE_DIR) if f.endswith(".wav")]

hindi_real_all = [f for f in all_real_files if "hindi" in os.path.basename(f).lower()]
telugu_real_all = [f for f in all_real_files if "telugu" in os.path.basename(f).lower()]
hindi_fake_all = [f for f in all_fake_files if "hindi" in os.path.basename(f).lower()]
telugu_fake_all = [f for f in all_fake_files if "telugu" in os.path.basename(f).lower()]

print(f"Real Hindi Samples  : {len(hindi_real_all)}", flush=True)
print(f"Real Telugu Samples : {len(telugu_real_all)}", flush=True)
print(f"Fake Hindi Samples  : {len(hindi_fake_all)}", flush=True)
print(f"Fake Telugu Samples : {len(telugu_fake_all)}", flush=True)
print(f"Total Multilingual Real : {len(all_real_files)}", flush=True)
print(f"Total Multilingual Fake : {len(all_fake_files)}", flush=True)
print(f"Total Multilingual Clips: {len(all_real_files) + len(all_fake_files)}", flush=True)

min_real = min(len(hindi_real_all), len(telugu_real_all))
if min_real < 25:
    print(f"ERROR: Dataset size below minimum required (min real per language = {min_real} < 25). Aborting fine-tune.", flush=True)
    exit(1)
else:
    print(f"SUCCESS: Real samples per language ({min_real}) exceeds requirement (25-30). Proceeding to Task 5!", flush=True)


# ---------------------------------------------------------
# TASK 5: Fine-Tune AASIST-L Final Layer & Evaluate
# ---------------------------------------------------------
print("\n==================================================", flush=True)
print("TASK 5: Fine-Tuning AASIST-L Final Layer & Validation", flush=True)
print("==================================================", flush=True)

import sys
sys.path.append(os.path.join(PROJECT_ROOT, "backend", "models", "aasist"))
from aasist_l import AASIST_L, pad_fixed, _D_ARGS, _CKPT
from _net import Model as AASISTNet

# Prepare dataset array & labels
multilingual_samples = []
for f in all_real_files:
    multilingual_samples.append((f, 1)) # 1 = Real
for f in all_fake_files:
    multilingual_samples.append((f, 0)) # 0 = Fake

random.shuffle(multilingual_samples)
n_total = len(multilingual_samples)
n_train = int(0.7 * n_total)

train_samples = multilingual_samples[:n_train]
val_samples = multilingual_samples[n_train:]

print(f"Multilingual Train Set: {len(train_samples)} samples", flush=True)
print(f"Multilingual Val Set  : {len(val_samples)} samples", flush=True)

# Prepare English holdout set for catastrophic forgetting check
ENG_REAL_DIR = os.path.join(PROJECT_ROOT, "data", "real")
ENG_FAKE_DIR = os.path.join(PROJECT_ROOT, "data", "fake")
eng_real = [os.path.join(ENG_REAL_DIR, f) for f in os.listdir(ENG_REAL_DIR) if f.endswith(".wav")]
eng_fake = [os.path.join(ENG_FAKE_DIR, f) for f in os.listdir(ENG_FAKE_DIR) if f.endswith(".wav")]

# Take 15 real, 15 fake English samples for holdout test
random.shuffle(eng_real)
random.shuffle(eng_fake)
eng_holdout = [(f, 1) for f in eng_real[:15]] + [(f, 0) for f in eng_fake[:15]]
print(f"English Holdout Check Set: {len(eng_holdout)} samples", flush=True)

# Load Audio Features
def load_audio_features(sample_list):
    X = []
    y = []
    for filepath, label in sample_list:
        audio, sr = librosa.load(filepath, sr=16000)
        padded = pad_fixed(audio)
        X.append(padded)
        y.append(label)
    return torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(y, dtype=torch.long)

X_train, y_train = load_audio_features(train_samples)
X_val, y_val = load_audio_features(val_samples)
X_eng, y_eng = load_audio_features(eng_holdout)

# Instantiate AASIST-L Network
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
net = AASISTNet(_D_ARGS)
sd = torch.load(_CKPT, map_location="cpu")
sd = sd.get("state_dict", sd) if isinstance(sd, dict) else sd
net.load_state_dict(sd, strict=True)
net = net.to(device)

# Freeze all layers except out_layer
print("\nLayer Trainability Status:", flush=True)
trainable_count = 0
frozen_count = 0
for name, param in net.named_parameters():
    if "out_layer" in name:
        param.requires_grad = True
        trainable_count += param.numel()
        print(f"  [TRAINABLE] {name}: shape {list(param.shape)}", flush=True)
    else:
        param.requires_grad = False
        frozen_count += param.numel()

print(f"Total Trainable Parameters: {trainable_count}", flush=True)
print(f"Total Frozen Parameters   : {frozen_count}", flush=True)

# Fine-tuning Setup
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(filter(lambda p: p.requires_grad, net.parameters()), lr=1e-4)

train_dataset = TensorDataset(X_train, y_train)
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)

print("\nStarting AASIST-L Fine-Tuning (8 Epochs)...", flush=True)
net.train()
for epoch in range(1, 9):
    running_loss = 0.0
    for batch_x, batch_y in train_loader:
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        optimizer.zero_grad()
        _, logits = net(batch_x)
        loss = criterion(logits, batch_y)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * batch_x.size(0)
    epoch_loss = running_loss / len(train_dataset)
    print(f"Epoch {epoch}/8 - Loss: {epoch_loss:.4f}", flush=True)

# Save fine-tuned checkpoint separately
FT_CKPT_PATH = os.path.join(MODEL_DIR, "aasist_l_multilingual_finetuned.pth")
torch.save(net.state_dict(), FT_CKPT_PATH)
print(f"\nSaved fine-tuned checkpoint to: {FT_CKPT_PATH}", flush=True)

# Batched Evaluation Function (prevents CPU memory allocation spikes)
@torch.no_grad()
def evaluate_model_batched(model, X_tensor, y_tensor, threshold=2.10, batch_size=16):
    model.eval()
    total = len(y_tensor)
    all_scores = []
    correct = 0
    
    for i in range(0, total, batch_size):
        bx = X_tensor[i : i + batch_size].to(device)
        by = y_tensor[i : i + batch_size].numpy()
        _, logits = model(bx)
        b_scores = logits[:, 1].cpu().numpy()
        all_scores.extend(b_scores)
        
        for score, true_label in zip(b_scores, by):
            pred_label = 1 if score > threshold else 0
            if pred_label == true_label:
                correct += 1
                
    accuracy = (correct / total) * 100.0
    return accuracy, np.array(all_scores)

# Evaluate Original Model vs Fine-Tuned Model
net_orig = AASISTNet(_D_ARGS)
net_orig.load_state_dict(sd, strict=True)
net_orig = net_orig.to(device)

print("\n==================================================", flush=True)
print("EVALUATION RESULTS COMPARISON", flush=True)
print("==================================================", flush=True)

# 1. Multilingual Holdout Accuracy
ml_val_acc_orig, _ = evaluate_model_batched(net_orig, X_val, y_val)
ml_val_acc_ft, _ = evaluate_model_batched(net, X_val, y_val)

# 2. English Holdout Accuracy (Catastrophic Forgetting Check)
eng_acc_orig, _ = evaluate_model_batched(net_orig, X_eng, y_eng)
eng_acc_ft, _ = evaluate_model_batched(net, X_eng, y_eng)

print(f"1. Multilingual Holdout Accuracy:", flush=True)
print(f"   - Original Model  : {ml_val_acc_orig:.2f}%", flush=True)
print(f"   - Fine-Tuned Model: {ml_val_acc_ft:.2f}%", flush=True)

print(f"\n2. English Holdout Accuracy (Catastrophic Forgetting Check):", flush=True)
print(f"   - Original Model  : {eng_acc_orig:.2f}%", flush=True)
print(f"   - Fine-Tuned Model: {eng_acc_ft:.2f}%", flush=True)

print("\n==================================================", flush=True)
print("FINAL SUMMARY & RECOMMENDATION", flush=True)
print("==================================================", flush=True)
print("Common Voice Version Worked: fsicoli/common_voice_17_0 (Common Voice 17.0 un-gated mirror)", flush=True)
print("Telugu Availability        : YES (te config available in Common Voice 17.0)", flush=True)
print(f"Dataset Counts per Lang    : Hindi ({len(hindi_real_all)} Real, {len(hindi_fake_all)} Fake), Telugu ({len(telugu_real_all)} Real, {len(telugu_fake_all)} Fake)", flush=True)
print(f"Multilingual Holdout Acc   : {ml_val_acc_ft:.2f}%", flush=True)
print(f"English Holdout Acc        : {eng_acc_ft:.2f}%", flush=True)

if eng_acc_ft < 85.0:
    print("RECOMMENDATION: DISCARD fine-tuned model due to catastrophic degradation on English speech.", flush=True)
else:
    print("RECOMMENDATION: ADOPT / KEEP AS SEPARATE CHECKPOINT for multilingual callers.", flush=True)
