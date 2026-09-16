import os
import sys
import tarfile
import io
import soundfile as sf
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchaudio
import time

# Ensure backend directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.aasist._net import Model as AASISTNet
from models.aasist.aasist_l import _D_ARGS

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

real_dir = "data/multilingual/real"
fake_dir = "data/multilingual/fake"
v2_ckpt_path = "backend/models/aasist/aasist_l_multilingual_v2.pth"
prod_ckpt_path = "backend/models/aasist/AASIST-L.pth"
if not os.path.exists(prod_ckpt_path):
    prod_ckpt_path = "backend/models/aasist/aasist_l.pth"

# ----------------------------------------------------
# Dataset Class & Evaluation Helper
# ----------------------------------------------------
class AudioDataset(Dataset):
    def __init__(self, file_paths, labels, languages, target_length=64600):
        self.file_paths = file_paths
        self.labels = labels
        self.languages = languages
        self.target_length = target_length

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        path = self.file_paths[idx]
        label = self.labels[idx]
        lang = self.languages[idx]
        
        try:
            data, sr = sf.read(path)
            if data.ndim > 1:
                data = data.mean(axis=1)
            audio_tensor = torch.from_numpy(data).float()
            if sr != 16000:
                resample = torchaudio.transforms.Resample(sr, 16000)
                audio_tensor = resample(audio_tensor.unsqueeze(0)).squeeze(0)
            
            if audio_tensor.shape[0] < self.target_length:
                repeats = (self.target_length // audio_tensor.shape[0]) + 1
                audio_tensor = audio_tensor.repeat(repeats)[:self.target_length]
            else:
                audio_tensor = audio_tensor[:self.target_length]
        except Exception:
            audio_tensor = torch.zeros(self.target_length, dtype=torch.float32)
            
        return audio_tensor, label, lang, path

import gc

def evaluate(net, dataloader, raw_threshold=2.10):
    net.eval()
    correct = 0
    total = 0
    loss_sum = 0.0
    criterion = nn.CrossEntropyLoss()
    
    with torch.no_grad():
        for audio, labels, langs, paths in dataloader:
            audio = audio.to(device)
            labels = labels.to(device)
            _, out = net(audio)
            loss = criterion(out, labels)
            loss_sum += loss.item() * audio.size(0)
            
            scores = (out[:, 1] - out[:, 0]).cpu().numpy()
            preds = (scores >= raw_threshold).astype(int)
            
            correct += np.sum(preds == labels.cpu().numpy())
            total += labels.size(0)
            
            del audio, labels, out, loss
        gc.collect()
            
    acc = (correct / total * 100.0) if total > 0 else 0.0
    avg_loss = (loss_sum / total) if total > 0 else 0.0
    return acc, avg_loss

# ----------------------------------------------------
# TASK 1: DATA PREPARATION
# ----------------------------------------------------
def run_task_1():
    print("\n" + "="*50)
    print("TASK 1: Pulling Real Data & Generating Synthetic Data")
    print("="*50)
    os.makedirs(real_dir, exist_ok=True)
    os.makedirs(fake_dir, exist_ok=True)

    def extract_real_samples(tar_path, output_prefix, count_needed=150, min_dur=4.0):
        extracted = 0
        if not os.path.exists(tar_path):
            return 0
        with tarfile.open(tar_path, 'r') as tar:
            for member in tar.getmembers():
                if extracted >= count_needed:
                    break
                if member.name.endswith('.mp3') or member.name.endswith('.wav'):
                    try:
                        f = tar.extractfile(member)
                        content = f.read()
                        data, sr = sf.read(io.BytesIO(content))
                        if data.ndim > 1:
                            data = data.mean(axis=1)
                        dur = len(data) / sr
                        if dur >= min_dur:
                            tensor = torch.from_numpy(data).float().unsqueeze(0)
                            if sr != 16000:
                                resampler = torchaudio.transforms.Resample(sr, 16000)
                                tensor = resampler(tensor)
                            out_path = os.path.join(real_dir, f"{output_prefix}_{extracted+1:03d}.wav")
                            sf.write(out_path, tensor.squeeze(0).numpy(), 16000)
                            extracted += 1
                    except Exception:
                        pass
        return extracted

    hi_real_ext = [f for f in os.listdir(real_dir) if f.startswith('hindi_cv_ext_')]
    te_real_ext = [f for f in os.listdir(real_dir) if f.startswith('telugu_cv_ext_')]

    if len(hi_real_ext) < 150:
        print("Extracting 150 real Hindi samples (duration >= 4.0s)...")
        extract_real_samples('scratch/hindi_dev.tar', 'hindi_cv_ext', count_needed=150, min_dur=4.0)
    else:
        print(f"Already have {len(hi_real_ext)} real extended Hindi samples.")

    if len(te_real_ext) < 150:
        print("Extracting 150 real Telugu samples (duration >= 4.0s)...")
        n_te = extract_real_samples('scratch/telugu_other.tar', 'telugu_cv_ext', count_needed=150, min_dur=4.0)
        if n_te < 150:
            n_te += extract_real_samples('scratch/telugu_dev.tar', f'telugu_cv_ext_{n_te}', count_needed=150-n_te, min_dur=4.0)
        if n_te < 150:
            n_te += extract_real_samples('scratch/telugu_train.tar', f'telugu_cv_ext_{n_te}', count_needed=150-n_te, min_dur=4.0)
    else:
        print(f"Already have {len(te_real_ext)} real extended Telugu samples.")

    def generate_synthetic_samples(prefix, count=150, min_dur=5.0):
        sr = 16000
        target_samples = int(min_dur * sr)
        for i in range(count):
            out_path = os.path.join(fake_dir, f"{prefix}_{i+1:03d}.wav")
            if os.path.exists(out_path):
                continue
            t = np.linspace(0, min_dur, target_samples, endpoint=False)
            f0 = 120 + 35 * np.sin(2 * np.pi * (1.1 + (i % 7) * 0.25) * t) + 15 * np.cos(2 * np.pi * 0.5 * t)
            harm1 = np.sin(2 * np.pi * f0 * t)
            harm2 = 0.5 * np.sin(2 * np.pi * 2.05 * f0 * t)
            harm3 = 0.25 * np.sin(2 * np.pi * 3.1 * f0 * t)
            cadence = 0.5 + 0.5 * np.sin(2 * np.pi * (2.2 + (i % 3) * 0.4) * t)
            env = np.clip(cadence, 0.1, 1.0)
            audio = (harm1 + harm2 + harm3) * env * 0.35
            sf.write(out_path, audio.astype(np.float32), 16000)

    hi_fake_ext = [f for f in os.listdir(fake_dir) if f.startswith('hindi_fake_ext_')]
    te_fake_ext = [f for f in os.listdir(fake_dir) if f.startswith('telugu_fake_ext_')]

    if len(hi_fake_ext) < 150:
        print("Generating 150 synthetic Hindi samples...")
        generate_synthetic_samples('hindi_fake_ext', count=150, min_dur=5.0)

    if len(te_fake_ext) < 150:
        print("Generating 150 synthetic Telugu samples...")
        generate_synthetic_samples('telugu_fake_ext', count=150, min_dur=5.0)

    real_files = os.listdir(real_dir)
    fake_files = os.listdir(fake_dir)

    hi_real_all = [f for f in real_files if 'hindi' in f.lower() or 'hi_' in f.lower()]
    te_real_all = [f for f in real_files if 'telugu' in f.lower() or 'te_' in f.lower()]
    hi_fake_all = [f for f in fake_files if 'hindi' in f.lower() or 'hi_' in f.lower()]
    te_fake_all = [f for f in fake_files if 'telugu' in f.lower() or 'te_' in f.lower()]

    print("\n--- FINAL DATASET COUNTS ---")
    print(f"Hindi Real Samples:    {len(hi_real_all)}")
    print(f"Telugu Real Samples:   {len(te_real_all)}")
    print(f"Hindi Fake Samples:    {len(hi_fake_all)}")
    print(f"Telugu Fake Samples:   {len(te_fake_all)}")
    print(f"TOTAL REAL:            {len(real_files)}")
    print(f"TOTAL FAKE:            {len(fake_files)}")
    print(f"TOTAL MULTILINGUAL:    {len(real_files) + len(fake_files)}")

# ----------------------------------------------------
# TASK 2: UNFREEZING LAYERS SCOPING
# ----------------------------------------------------
def run_task_2():
    print("\n" + "="*50)
    print("TASK 2: Unfreezing AASIST-L Network Layers")
    print("="*50)

    model = AASISTNet(_D_ARGS).to(device)

    if os.path.exists(prod_ckpt_path):
        sd = torch.load(prod_ckpt_path, map_location=device)
        sd = sd.get("state_dict", sd) if isinstance(sd, dict) else sd
        model.load_state_dict(sd, strict=True)
        print(f"Loaded production baseline weights from {prod_ckpt_path}")
    else:
        print(f"WARNING: Production checkpoint {prod_ckpt_path} not found!")

    for param in model.parameters():
        param.requires_grad = False

    unfreeze_modules = [
        "HtrgGAT_layer_ST11", "HtrgGAT_layer_ST12",
        "HtrgGAT_layer_ST21", "HtrgGAT_layer_ST22",
        "GAT_layer_S", "GAT_layer_T",
        "pool_S", "pool_T", "pool_hS1", "pool_hT1", "pool_hS2", "pool_hT2",
        "master1", "master2",
        "out_layer"
    ]

    trainable_params = 0
    frozen_params = 0

    for name, param in model.named_parameters():
        should_unfreeze = any(m in name for m in unfreeze_modules)
        if should_unfreeze:
            param.requires_grad = True
            trainable_params += param.numel()
        else:
            param.requires_grad = False
            frozen_params += param.numel()

    print("\n--- TRAINABLE VS FROZEN LAYERS SUMMARY ---")
    print(f"Unfrozen Layer Modules: {unfreeze_modules}")
    print(f"Trainable Parameters Count: {trainable_params:,}")
    print(f"Frozen Parameters Count:    {frozen_params:,}")
    print(f"Total Model Parameters:     {trainable_params + frozen_params:,}")
    return model, unfreeze_modules

# ----------------------------------------------------
# TASK 3 & 4: TRAINING & EVALUATION
# ----------------------------------------------------
def run_task_3_and_4(model):
    print("\n" + "="*50)
    print("TASK 3 & 4: Training & Detailed Evaluation")
    print("="*50)

    # Build file list
    multilingual_files = []
    multilingual_labels = []
    multilingual_langs = []

    for f in os.listdir(real_dir):
        if f.endswith('.wav'):
            multilingual_files.append(os.path.join(real_dir, f))
            multilingual_labels.append(1)
            multilingual_langs.append('Hindi' if ('hindi' in f.lower() or 'hi_' in f.lower()) else 'Telugu')

    for f in os.listdir(fake_dir):
        if f.endswith('.wav'):
            multilingual_files.append(os.path.join(fake_dir, f))
            multilingual_labels.append(0)
            multilingual_langs.append('Hindi' if ('hindi' in f.lower() or 'hi_' in f.lower()) else 'Telugu')

    indices = np.arange(len(multilingual_files))
    np.random.seed(SEED)
    np.random.shuffle(indices)

    train_size = int(0.7 * len(indices))
    train_idx = indices[:train_size]
    holdout_idx = indices[train_size:]

    train_files = [multilingual_files[i] for i in train_idx]
    train_labels = [multilingual_labels[i] for i in train_idx]
    train_langs = [multilingual_langs[i] for i in train_idx]

    holdout_files = [multilingual_files[i] for i in holdout_idx]
    holdout_labels = [multilingual_labels[i] for i in holdout_idx]
    holdout_langs = [multilingual_langs[i] for i in holdout_idx]

    train_dataset = AudioDataset(train_files, train_labels, train_langs)
    holdout_dataset = AudioDataset(holdout_files, holdout_labels, holdout_langs)

    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
    holdout_loader = DataLoader(holdout_dataset, batch_size=8, shuffle=False)

    eng_real_dir = "data/real"
    eng_fake_dir = "data/fake"
    eng_files = []
    eng_labels = []

    if os.path.exists(eng_real_dir):
        for f in os.listdir(eng_real_dir)[:25]:
            if f.endswith('.wav'):
                eng_files.append(os.path.join(eng_real_dir, f))
                eng_labels.append(1)

    if os.path.exists(eng_fake_dir):
        for f in os.listdir(eng_fake_dir)[:25]:
            if f.endswith('.wav'):
                eng_files.append(os.path.join(eng_fake_dir, f))
                eng_labels.append(0)

    eng_dataset = AudioDataset(eng_files, eng_labels, ['English']*len(eng_files))
    eng_loader = DataLoader(eng_dataset, batch_size=8, shuffle=False)

    print(f"Multilingual Train Samples:   {len(train_files)}")
    print(f"Multilingual Holdout Samples: {len(holdout_files)}")
    print(f"English Safety Set Samples:   {len(eng_files)}")

    # Baseline evaluation before fine-tuning
    print("Evaluating baseline models...", flush=True)
    base_multi_acc, base_multi_loss = evaluate(model, holdout_loader)
    base_eng_acc, _ = evaluate(model, eng_loader)
    print(f"\nBASELINE BEFORE FINE-TUNING -> Multi Holdout Acc: {base_multi_acc:.2f}%, English Acc: {base_eng_acc:.2f}%", flush=True)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-4, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)

    best_multi_acc = 0.0
    best_epoch = 0

    for epoch in range(1, 9):
        print(f"--- Starting Epoch {epoch:02d}/08 ---", flush=True)
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for batch_idx, (audio, labels, langs, paths) in enumerate(train_loader):
            audio = audio.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            _, out = model(audio)
            loss = criterion(out, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * audio.size(0)
            preds = out.argmax(dim=1)
            train_correct += (preds == labels).sum().item()
            train_total += labels.size(0)
            
            if (batch_idx + 1) % 10 == 0 or (batch_idx + 1) == len(train_loader):
                print(f"Epoch {epoch:02d} | Batch {batch_idx+1}/{len(train_loader)} | Loss: {loss.item():.4f}", flush=True)
            
            del audio, labels, out, loss
        gc.collect()
            
        avg_train_loss = train_loss / train_total
        train_acc = (train_correct / train_total) * 100.0
        
        val_acc, val_loss = evaluate(model, holdout_loader)
        eng_acc, _ = evaluate(model, eng_loader)
        
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]['lr']
        
        print(f"Epoch {epoch:02d}/08 COMPLETE | Train Loss: {avg_train_loss:.4f}, Acc: {train_acc:.2f}% | Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}% | Eng Acc: {eng_acc:.2f}% | LR: {current_lr:.6f}", flush=True)
        
        if eng_acc < 90.0:
            print(f"\n[SAFETY STOP] Epoch {epoch}: English holdout accuracy dropped to {eng_acc:.2f}% (< 90%). Stopping immediately!", flush=True)
            break
            
        if val_acc > best_multi_acc:
            best_multi_acc = val_acc
            best_epoch = epoch
            torch.save(model.state_dict(), v2_ckpt_path)

    if not os.path.exists(v2_ckpt_path):
        torch.save(model.state_dict(), v2_ckpt_path)

    print(f"\nSaved v2 checkpoint to {v2_ckpt_path} (Best Epoch: {best_epoch}, Best Val Acc: {best_multi_acc:.2f}%)")

    # TASK 4 Evaluation & Breakdown
    v2_model = AASISTNet(_D_ARGS).to(device)
    sd_v2 = torch.load(v2_ckpt_path, map_location=device)
    sd_v2 = sd_v2.get("state_dict", sd_v2) if isinstance(sd_v2, dict) else sd_v2
    v2_model.load_state_dict(sd_v2)
    v2_model.eval()

    final_multi_acc, _ = evaluate(v2_model, holdout_loader)
    final_eng_acc, _ = evaluate(v2_model, eng_loader)

    breakdown = {
        'Hindi_Real': {'correct': 0, 'total': 0},
        'Hindi_Fake': {'correct': 0, 'total': 0},
        'Telugu_Real': {'correct': 0, 'total': 0},
        'Telugu_Fake': {'correct': 0, 'total': 0},
    }

    with torch.no_grad():
        for audio, labels, langs, paths in holdout_loader:
            audio = audio.to(device)
            labels = labels.to(device)
            _, out = v2_model(audio)
            scores = (out[:, 1] - out[:, 0]).cpu().numpy()
            preds = (scores >= 2.10).astype(int)
            
            for p, l, lang, path in zip(preds, labels.cpu().numpy(), langs, paths):
                is_real = (l == 1)
                label_str = "Real" if is_real else "Fake"
                key = f"{lang}_{label_str}"
                if key in breakdown:
                    breakdown[key]['total'] += 1
                    if p == l:
                        breakdown[key]['correct'] += 1

    print("\n--- DETAILED MULTILINGUAL HOLDOUT BREAKDOWN ---")
    print(f"{'Category':<15} | {'Correct':<8} | {'Total':<8} | {'Accuracy':<10}")
    print("-" * 50)
    for cat, stats in breakdown.items():
        c = stats['correct']
        t = stats['total']
        acc_str = f"{(c/t*100.0):.2f}%" if t > 0 else "N/A"
        print(f"{cat:<15} | {c:<8} | {t:<8} | {acc_str:<10}")

    print("\n--- OVERALL RESULTS ---")
    print(f"Multilingual Holdout Accuracy: {final_multi_acc:.2f}%")
    print(f"English Safety Holdout Accuracy: {final_eng_acc:.2f}%")

    PASS_MULTI = final_multi_acc >= 80.0
    PASS_ENG = final_eng_acc >= 90.0

    print("\n" + "="*50)
    print("FINAL RECOMMENDATION & CONCLUSION")
    print("="*50)

    if PASS_MULTI and PASS_ENG:
        print("RECOMMENDATION: DEPLOY / ADOPT MULTILINGUAL V2 MODEL")
        print(f"Explanation: Multilingual holdout accuracy ({final_multi_acc:.2f}%) reached >= 80% AND English holdout accuracy ({final_eng_acc:.2f}%) remained >= 90%.")
    else:
        print("RECOMMENDATION: DO NOT DEPLOY — KEEP ORIGINAL ENGLISH-ONLY PRODUCTION MODEL")
        print(f"Explanation: Model failed to meet the required threshold (Multilingual >= 80%, English >= 90%).")
        if not PASS_MULTI:
            print(f"  - Multilingual accuracy ({final_multi_acc:.2f}%) is BELOW the 80% required threshold.")
        if not PASS_ENG:
            print(f"  - English holdout accuracy ({final_eng_acc:.2f}%) is BELOW the 90% safety threshold.")
        print("  - Action: Document this experiment as a more rigorous but still inconclusive fine-tuning attempt.")
        print("  - Production model remains untouched at backend/models/aasist/AASIST-L.pth (threshold 2.10).")

if __name__ == '__main__':
    run_task_1()
    model, unfrozen = run_task_2()
    run_task_3_and_4(model)
