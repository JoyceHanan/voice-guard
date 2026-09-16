import os
import sys
import numpy as np
import soundfile as sf
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchaudio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.aasist._net import Model as AASISTNet
from models.aasist.aasist_l import _D_ARGS

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

real_dir = "data/multilingual/real"
fake_dir = "data/multilingual/fake"
v2_ckpt_path = "backend/models/aasist/aasist_l_multilingual_v2.pth"

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

# Build file list
multilingual_files = []
multilingual_labels = []
multilingual_langs = []

for f in sorted(os.listdir(real_dir)):
    if f.endswith('.wav'):
        multilingual_files.append(os.path.join(real_dir, f))
        multilingual_labels.append(1)
        multilingual_langs.append('Hindi' if ('hindi' in f.lower() or 'hi_' in f.lower()) else 'Telugu')

for f in sorted(os.listdir(fake_dir)):
    if f.endswith('.wav'):
        multilingual_files.append(os.path.join(fake_dir, f))
        multilingual_labels.append(0)
        multilingual_langs.append('Hindi' if ('hindi' in f.lower() or 'hi_' in f.lower()) else 'Telugu')

indices = np.arange(len(multilingual_files))
np.random.seed(SEED)
np.random.shuffle(indices)

train_size = int(0.7 * len(indices))
holdout_idx = indices[train_size:]

holdout_files = [multilingual_files[i] for i in holdout_idx]
holdout_labels = [multilingual_labels[i] for i in holdout_idx]
holdout_langs = [multilingual_langs[i] for i in holdout_idx]

holdout_dataset = AudioDataset(holdout_files, holdout_labels, holdout_langs)
holdout_loader = DataLoader(holdout_dataset, batch_size=8, shuffle=False)

eng_real_dir = "data/real"
eng_fake_dir = "data/fake"
eng_files = []
eng_labels = []

if os.path.exists(eng_real_dir):
    for f in sorted(os.listdir(eng_real_dir))[:25]:
        if f.endswith('.wav'):
            eng_files.append(os.path.join(eng_real_dir, f))
            eng_labels.append(1)

if os.path.exists(eng_fake_dir):
    for f in sorted(os.listdir(eng_fake_dir))[:25]:
        if f.endswith('.wav'):
            eng_files.append(os.path.join(eng_fake_dir, f))
            eng_labels.append(0)

eng_dataset = AudioDataset(eng_files, eng_labels, ['English']*len(eng_files))
eng_loader = DataLoader(eng_dataset, batch_size=8, shuffle=False)

# Load v2 model checkpoint
model = AASISTNet(_D_ARGS).to(device)
sd = torch.load(v2_ckpt_path, map_location=device)
sd = sd.get("state_dict", sd) if isinstance(sd, dict) else sd
model.load_state_dict(sd)
model.eval()

# Multilingual Evaluation & Detailed Breakdown
breakdown = {
    'Hindi_Real': {'correct': 0, 'total': 0},
    'Hindi_Fake': {'correct': 0, 'total': 0},
    'Telugu_Real': {'correct': 0, 'total': 0},
    'Telugu_Fake': {'correct': 0, 'total': 0},
}

multi_correct = 0
multi_total = 0

with torch.no_grad():
    for audio, labels, langs, paths in holdout_loader:
        audio = audio.to(device)
        labels = labels.to(device)
        _, out = model(audio)
        scores = (out[:, 1] - out[:, 0]).cpu().numpy()
        preds = (scores >= 2.10).astype(int)
        
        for p, l, lang in zip(preds, labels.cpu().numpy(), langs):
            multi_total += 1
            if p == l:
                multi_correct += 1
            is_real = (l == 1)
            label_str = "Real" if is_real else "Fake"
            key = f"{lang}_{label_str}"
            if key in breakdown:
                breakdown[key]['total'] += 1
                if p == l:
                    breakdown[key]['correct'] += 1

multi_acc = (multi_correct / multi_total * 100.0) if multi_total > 0 else 0.0

# English Holdout Evaluation
eng_correct = 0
eng_total = 0
with torch.no_grad():
    for audio, labels, langs, paths in eng_loader:
        audio = audio.to(device)
        labels = labels.to(device)
        _, out = model(audio)
        scores = (out[:, 1] - out[:, 0]).cpu().numpy()
        preds = (scores >= 2.10).astype(int)
        
        for p, l in zip(preds, labels.cpu().numpy()):
            eng_total += 1
            if p == l:
                eng_correct += 1

eng_acc = (eng_correct / eng_total * 100.0) if eng_total > 0 else 0.0

print("\n" + "="*60)
print("AASIST-L MULTILINGUAL FINE-TUNING V2 EVALUATION REPORT")
print("="*60)
print(f"Multilingual Holdout Accuracy: {multi_acc:.2f}% ({multi_correct}/{multi_total})")
print(f"English Holdout Safety Accuracy: {eng_acc:.2f}% ({eng_correct}/{eng_total})")

print("\n--- DETAILED BREAKDOWN BY LANGUAGE & CLASS ---")
print(f"{'Category':<15} | {'Correct':<8} | {'Total':<8} | {'Accuracy':<10}")
print("-" * 50)
for cat, stats in breakdown.items():
    c = stats['correct']
    t = stats['total']
    acc_str = f"{(c/t*100.0):.2f}%" if t > 0 else "N/A"
    print(f"{cat:<15} | {c:<8} | {t:<8} | {acc_str:<10}")

PASS_MULTI = multi_acc >= 80.0
PASS_ENG = eng_acc >= 90.0

print("\n" + "="*60)
print("FINAL DEPLOYMENT RECOMMENDATION & CONCLUSION")
print("="*60)

if PASS_MULTI and PASS_ENG:
    print("RECOMMENDATION: GENUINELY USABLE MULTILINGUAL CAPABILITY (DEPLOY V2 MODEL)")
    print(f"  - Multilingual holdout accuracy ({multi_acc:.2f}%) met/exceeded the >= 80% threshold.")
    print(f"  - English holdout accuracy ({eng_acc:.2f}%) met/exceeded the >= 90% threshold.")
    print(f"  - Checkpoint saved as: {v2_ckpt_path}")
else:
    print("RECOMMENDATION: INSUFFICIENT FOR PRODUCTION — KEEP ORIGINAL ENGLISH-ONLY MODEL")
    print(f"  - Multilingual accuracy ({multi_acc:.2f}%) threshold requirement (>= 80%): {'PASS' if PASS_MULTI else 'FAIL'}")
    print(f"  - English accuracy ({eng_acc:.2f}%) threshold requirement (>= 90%): {'PASS' if PASS_ENG else 'FAIL'}")
    print("  - Action: Retain original production checkpoint backend/models/aasist/AASIST-L.pth (threshold 2.10).")
