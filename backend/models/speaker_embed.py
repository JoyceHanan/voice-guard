"""VoiceGuard Speaker Embedding Module.

Uses SpeechBrain ECAPA-TDNN (spkrec-ecapa-voxceleb) model to extract 192-dim speaker embeddings
and compute cosine similarity between audio samples.
"""

import os
from pathlib import Path
import torch
import torchaudio
from speechbrain.inference.speaker import EncoderClassifier
from speechbrain.utils.fetching import LocalStrategy

_MODEL_CACHE = None
SAVEDIR = Path(__file__).resolve().parent / "spkrec-ecapa-voxceleb"


def load_speaker_model():
    """Load or retrieve cached ECAPA-TDNN speaker embedding model."""
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        os.makedirs(SAVEDIR, exist_ok=True)
        _MODEL_CACHE = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=str(SAVEDIR),
            run_opts={"device": device},
            local_strategy=LocalStrategy.COPY,
        )
    return _MODEL_CACHE


import soundfile as sf
import librosa
import numpy as np

def compute_embedding(wav_path: str) -> torch.Tensor:
    """Load WAV/audio file using soundfile (with librosa fallback) and return a 1D PyTorch tensor speaker embedding vector."""
    classifier = load_speaker_model()
    try:
        data, fs = sf.read(wav_path, dtype="float32")
    except Exception:
        # Fallback to librosa for MP3/WebM/OGG files
        data, fs = librosa.load(wav_path, sr=None, mono=False)
        if data.dtype != np.float32:
            data = data.astype(np.float32)

    # Convert numpy data to PyTorch tensor (shape: channels x samples)
    if data.ndim == 1:
        signal = torch.from_numpy(data).unsqueeze(0)
    else:
        signal = torch.from_numpy(data.T if data.shape[0] != 1 and data.shape[1] == 1 else data)
        if signal.ndim == 1:
            signal = signal.unsqueeze(0)

    # Convert to mono if multi-channel
    if signal.shape[0] > 1:
        signal = signal.mean(dim=0, keepdim=True)

    # Resample to 16kHz if necessary
    if fs != 16000:
        resampler = torchaudio.transforms.Resample(fs, 16000)
        signal = resampler(signal)

    with torch.no_grad():
        embeddings = classifier.encode_batch(signal)

    # Return L2-normalized 1D embedding tensor
    emb = embeddings.squeeze()
    return torch.nn.functional.normalize(emb, p=2, dim=-1)


def compute_cosine_similarity(wav_path1: str, wav_path2: str) -> float:
    """Compute cosine similarity score between speaker embeddings of two audio files."""
    emb1 = compute_embedding(wav_path1)
    emb2 = compute_embedding(wav_path2)

    # Cosine similarity in range [-1.0, 1.0]
    cos = torch.nn.functional.cosine_similarity(emb1.unsqueeze(0), emb2.unsqueeze(0))
    return float(cos.item())
