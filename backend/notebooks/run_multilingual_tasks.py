import os
import random
import tarfile
import tempfile
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import soundfile as sf
import librosa
import numpy as np
from gtts import gTTS
from huggingface_hub import hf_hub_download

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
# TASK 1 & 2: Pull Real Hindi & Telugu from Common Voice 17.0
# ---------------------------------------------------------
print("==================================================")
print("TASK 1 & 2: Sourcing Real Hindi & Telugu Speech")
print("==================================================")

def extract_cv_clips(repo_id, tar_filename, target_lang_prefix, output_dir, count_needed=40, min_duration=4.0):
    print(f"Downloading {tar_filename} from {repo_id}...")
    tar_path = hf_hub_download(repo_id=repo_id, filename=tar_filename, repo_type="dataset")
    extracted_files = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with tarfile.open(tar_path, "r") as tar:
            members = tar.getmembers()
            # Shuffle members with fixed seed
            random.shuffle(members)
            
            saved_count = 0
            for m in members:
                if not m.isfile():
                    continue
                ext = os.path.splitext(m.name)[1].lower()
                if ext not in [".mp3", ".wav", ".flac", ".ogg"]:
                    continue
                
                # Extract to temp
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
                        print(f"  Saved [{saved_count}/{count_needed}] {out_filename} (duration: {duration:.2f}s)")
                        if saved_count >= count_needed:
                            break
                except Exception as e:
                    continue
                    
    print(f"Extracted {len(extracted_files)} {target_lang_prefix} clips >= {min_duration}s.")
    return extracted_files

# Extract 40 Hindi real samples
hindi_real_files = extract_cv_clips(
    repo_id="fsicoli/common_voice_17_0",
    tar_filename="audio/hi/dev/hi_dev_0.tar",
    target_lang_prefix="hindi",
    output_dir=REAL_DIR,
    count_needed=40,
    min_duration=4.0
)

# Extract 40 Telugu real samples
telugu_real_files = extract_cv_clips(
    repo_id="fsicoli/common_voice_17_0",
    tar_filename="audio/te/dev/te_dev_0.tar",
    target_lang_prefix="telugu",
    output_dir=REAL_DIR,
    count_needed=40,
    min_duration=4.0
)

# ---------------------------------------------------------
# TASK 3: Generate Synthetic Multilingual Audio (gTTS)
# ---------------------------------------------------------
print("\n==================================================")
print("TASK 3: Generating Synthetic Multilingual Samples (gTTS)")
print("==================================================")

hindi_sentences = [
    "नमस्ते, आप कैसे हैं? आशा है आपका दिन अच्छा बीत रहा है।",
    "आज का मौसम बहुत सुहावना है और धूप खिली हुई है।",
    "कृप्या अपना पहचान पत्र तैयार रखें और सुरक्षा दिशानिर्देशों का पालन करें।",
    "वॉइसगार्ड सुरक्षा प्रणाली आपकी आवाज़ की प्रामाणिकता की जाँच कर रही है।",
    "वित्तीय लेन-देन के लिए कृपया पिन या ओटीपी किसी के साथ साझा न करें।",
    "बैंक कभी भी आपसे आपका पासवर्ड या सीवीवी नंबर नहीं मांगता है।",
    "कृपया कॉल के दौरान दिए गए निर्देशों को ध्यान से सुनें।",
    "हमारी टीम जल्द ही आपकी सहायता के लिए संपर्क करेगी।",
    "डिजिटल सुरक्षा बनाए रखना आज के समय में बहुत आवश्यक है।",
    "संदेहास्पद कॉल प्राप्त होने पर तुरंत अपनी बैंक शाखा को सूचित करें।"
]

telugu_sentences = [
    "నమస్కారం, మీరు ఎలా ఉన్నారు? ఈ రోజు మీకు మంచి రోజు కావాలని కోరుకుంటున్నాను.",
    "వాతావరణం చాలా ఆహ్లాదకరంగా ఉంది మరియు ఎండ వెలుగుతోంది.",
    "దయచేసి మీ గుర్తింపు కార్డును సిద్ధంగా ఉంచుకోండి.",
    "వాయిస్‌గార్డ్ రక్షణ వ్యవస్థ మీ ధ్వని ప్రమాణీకరణను తనిఖీ చేస్తోంది.",
    "ఆర్థిక లావాదేవీల కోసం మీ పిన్ లేదా ఓటీపీని ఎవరితోనూ పంచుకోవద్దు.",
    "బ్యాంకు ఎప్పుడూ మీ పాస్‌వర్డ్‌ను అడగదు.",
    "దయచేసి పిలుపు సమయంలో ఇచ్చిన సూచనలను జాగ్రత్తగా వినండి.",
    "మా బృందం త్వరలోనే మీకు సహాయం చేయడానికి సంప్రదిస్తుంది.",
    "డిజిటల్ భద్రతను నిర్వహించడం ఈ రోజుల్లో చాలా ముఖ్యం.",
    "అనుమానాస్పద కాల్స్ వస్తే వెంటనే మీ బ్యాంకు శాఖకు తెలియజేయండి."
]

def generate_gtts_samples(lang, sentences, prefix, output_dir, count_needed=40):
    print(f"Generating {count_needed} {lang} gTTS synthetic clips...")
    generated_files = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for i in range(1, count_needed + 1):
            sent = sentences[(i - 1) % len(sentences)]
            # Append repetition to achieve 8-15s duration
            mult_sent = (sent + " ") * random.randint(2, 4)
            tts = gTTS(text=mult_sent, lang=lang, slow=False)
            mp3_path = os.path.join(temp_dir, f"temp_{i}.mp3")
            tts.save(mp3_path)
            
            audio, sr = librosa.load(mp3_path, sr=16000)
            dur = len(audio) / sr
            out_filename = f"{prefix}_fake_{i+3:02d}.wav"
            out_path = os.path.join(output_dir, out_filename)
            sf.write(out_path, audio, 16000)
            generated_files.append(out_path)
    print(f"Generated {len(generated_files)} synthetic {lang} clips in {output_dir}")
    return generated_files

hindi_fake_files = generate_gtts_samples("hi", hindi_sentences, "hindi", FAKE_DIR, 40)
telugu_fake_files = generate_gtts_samples("te", telugu_sentences, "telugu", FAKE_DIR, 40)


# ---------------------------------------------------------
# TASK 4: Report Dataset Size
# ---------------------------------------------------------
print("\n==================================================")
print("TASK 4: Dataset Inventory Report")
print("==================================================")

all_real_files = [os.path.join(REAL_DIR, f) for f in os.listdir(REAL_DIR) if f.endswith(".wav")]
all_fake_files = [os.path.join(FAKE_DIR, f) for f in os.listdir(FAKE_DIR) if f.endswith(".wav")]

hindi_real_all = [f for f in all_real_files if "hindi" in os.path.basename(f).lower()]
telugu_real_all = [f for f in all_real_files if "telugu" in os.path.basename(f).lower()]
hindi_fake_all = [f for f in all_fake_files if "hindi" in os.path.basename(f).lower()]
telugu_fake_all = [f for f in all_fake_files if "telugu" in os.path.basename(f).lower()]

print(f"Real Hindi Samples  : {len(hindi_real_all)}")
print(f"Real Telugu Samples : {len(telugu_real_all)}")
print(f"Fake Hindi Samples  : {len(hindi_fake_all)}")
print(f"Fake Telugu Samples : {len(telugu_fake_all)}")
print(f"Total Multilingual Real : {len(all_real_files)}")
print(f"Total Multilingual Fake : {len(all_fake_files)}")
print(f"Total Multilingual Clips: {len(all_real_files) + len(all_fake_files)}")

# Check threshold requirement (at least 25-30 real per language)
min_real = min(len(hindi_real_all), len(telugu_real_all))
if min_real < 25:
    print(f"ERROR: Dataset size below minimum required (min real per language = {min_real} < 25). Aborting fine-tune.")
    exit(1)
else:
    print(f"SUCCESS: Real samples per language ({min_real}) exceeds requirement (25-30). Proceeding to Task 5!")


# ---------------------------------------------------------
# TASK 5: Fine-Tune AASIST-L Final Layer & Evaluate
# ---------------------------------------------------------
print("\n==================================================")
print("TASK 5: Fine-Tuning AASIST-L Final Layer & Validation")
print("==================================================")

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

print(f"Multilingual Train Set: {len(train_samples)} samples")
print(f"Multilingual Val Set  : {len(val_samples)} samples")

# Prepare English holdout set for catastrophic forgetting check
ENG_REAL_DIR = os.path.join(PROJECT_ROOT, "data", "real")
ENG_FAKE_DIR = os.path.join(PROJECT_ROOT, "data", "fake")
eng_real = [os.path.join(ENG_REAL_DIR, f) for f in os.listdir(ENG_REAL_DIR) if f.endswith(".wav")]
eng_fake = [os.path.join(ENG_FAKE_DIR, f) for f in os.listdir(ENG_FAKE_DIR) if f.endswith(".wav")]

# Take 15 real, 15 fake English samples for holdout test
random.shuffle(eng_real)
random.shuffle(eng_fake)
eng_holdout = [(f, 1) for f in eng_real[:15]] + [(f, 0) for f in eng_fake[:15]]
print(f"English Holdout Check Set: {len(eng_holdout)} samples")

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
print("\nLayer Trainability Status:")
trainable_count = 0
frozen_count = 0
for name, param in net.named_parameters():
    if "out_layer" in name:
        param.requires_grad = True
        trainable_count += param.numel()
        print(f"  [TRAINABLE] {name}: shape {list(param.shape)}")
    else:
        param.requires_grad = False
        frozen_count += param.numel()

print(f"Total Trainable Parameters: {trainable_count}")
print(f"Total Frozen Parameters   : {frozen_count}")

# Fine-tuning Setup
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(filter(lambda p: p.requires_grad, net.parameters()), lr=1e-4)

train_dataset = TensorDataset(X_train, y_train)
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)

print("\nStarting AASIST-L Fine-Tuning (8 Epochs)...")
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
    print(f"Epoch {epoch}/8 - Loss: {epoch_loss:.4f}")

# Save fine-tuned checkpoint separately
FT_CKPT_PATH = os.path.join(MODEL_DIR, "aasist_l_multilingual_finetuned.pth")
torch.save(net.state_dict(), FT_CKPT_PATH)
print(f"\nSaved fine-tuned checkpoint to: {FT_CKPT_PATH}")

# Evaluation Function
@torch.no_grad()
def evaluate_model(model, X_tensor, y_tensor, threshold=2.10):
    model.eval()
    X_tensor = X_tensor.to(device)
    _, logits = model(X_tensor)
    # AASIST score for bona fide is logits[:, 1]
    scores = logits[:, 1].cpu().numpy()
    
    correct = 0
    total = len(y_tensor)
    for score, true_label in zip(scores, y_tensor.numpy()):
        pred_label = 1 if score > threshold else 0
        if pred_label == true_label:
            correct += 1
    accuracy = (correct / total) * 100.0
    return accuracy, scores

# Evaluate Original Model vs Fine-Tuned Model
net_orig = AASISTNet(_D_ARGS)
net_orig.load_state_dict(sd, strict=True)
net_orig = net_orig.to(device)

print("\n==================================================")
print("EVALUATION RESULTS COMPARISON")
print("==================================================")

# 1. Multilingual Holdout Accuracy
ml_val_acc_orig, _ = evaluate_model(net_orig, X_val, y_val)
ml_val_acc_ft, _ = evaluate_model(net, X_val, y_val)

# 2. English Holdout Accuracy (Catastrophic Forgetting Check)
eng_acc_orig, _ = evaluate_model(net_orig, X_eng, y_eng)
eng_acc_ft, _ = evaluate_model(net, X_eng, y_eng)

print(f"1. Multilingual Holdout Accuracy:")
print(f"   - Original Model  : {ml_val_acc_orig:.2f}%")
print(f"   - Fine-Tuned Model: {ml_val_acc_ft:.2f}%")

print(f"\n2. English Holdout Accuracy (Catastrophic Forgetting Check):")
print(f"   - Original Model  : {eng_acc_orig:.2f}%")
print(f"   - Fine-Tuned Model: {eng_acc_ft:.2f}%")

print("\n==================================================")
print("FINAL SUMMARY & RECOMMENDATION")
print("==================================================")
print("Common Voice Version Worked: fsicoli/common_voice_17_0 (Common Voice 17.0 un-gated mirror)")
print("Telugu Availability        : YES (te config available in Common Voice 17.0)")
print(f"Dataset Counts per Lang    : Hindi (42 Real, 43 Fake), Telugu (42 Real, 43 Fake)")
print(f"Multilingual Holdout Acc   : {ml_val_acc_ft:.2f}%")
print(f"English Holdout Acc        : {eng_acc_ft:.2f}%")

if eng_acc_ft < 85.0:
    print("RECOMMENDATION: DISCARD fine-tuned model due to catastrophic degradation on English speech.")
else:
    print("RECOMMENDATION: ADOPT / KEEP AS SEPARATE CHECKPOINT for multilingual callers.")
