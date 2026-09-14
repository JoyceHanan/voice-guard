"""VoiceGuard Audio Quality & Signal-to-Noise Ratio (SNR) Module.

Provides signal-processing heuristic to estimate SNR (in dB) and categorize
audio into "GOOD", "MODERATE", or "POOR" quality tiers.
"""

import numpy as np


def estimate_quality(audio_array: np.ndarray, sample_rate: int = 16000) -> tuple[str, float]:
    """Estimates Signal-to-Noise Ratio (SNR) in dB and returns (quality_label, snr_db).

    Algorithm:
    1. Frames the audio signal into 25ms frames with 10ms hop.
    2. Calculates Root-Mean-Square (RMS) energy for each frame.
    3. Noise floor estimate = mean RMS of the lowest 10% energy frames.
    4. Speech signal estimate = mean RMS of the highest 50% energy frames.
    5. SNR (dB) = 20 * log10(signal_rms / (noise_rms + 1e-8)).

    Recalibrated Quality Tiers:
    - "GOOD": SNR >= 30.0 dB (Clean, high-fidelity studio/close-mic speech)
    - "MODERATE": 15.0 dB <= SNR < 30.0 dB (Mild to noticeable background noise or room reverberation)
    - "POOR": SNR < 15.0 dB (Severe background noise or heavily degraded audio)
    """
    audio = np.asarray(audio_array, dtype=np.float32).reshape(-1)

    if len(audio) == 0:
        return ("POOR", 0.0)

    frame_size = int(sample_rate * 0.025)
    hop_size = int(sample_rate * 0.010)

    if len(audio) < frame_size:
        signal_rms = np.sqrt(np.mean(audio**2)) + 1e-8
        noise_rms = 1e-4
    else:
        num_frames = 1 + (len(audio) - frame_size) // hop_size
        frames = np.lib.stride_tricks.as_strided(
            audio,
            shape=(num_frames, frame_size),
            strides=(audio.strides[0] * hop_size, audio.strides[0]),
        )
        frame_rms = np.sqrt(np.mean(frames**2, axis=1) + 1e-10)
        sorted_rms = np.sort(frame_rms)

        # Lowest 10% frames -> noise floor estimate
        num_noise_frames = max(1, int(len(sorted_rms) * 0.10))
        noise_rms = np.mean(sorted_rms[:num_noise_frames])

        # Top 50% frames -> speech signal estimate
        num_signal_frames = max(1, int(len(sorted_rms) * 0.50))
        signal_rms = np.mean(sorted_rms[-num_signal_frames:])

    snr_db = 20.0 * np.log10(max(signal_rms, 1e-8) / max(noise_rms, 1e-8))
    snr_db = round(float(snr_db), 2)

    # Recalibrated Thresholds
    if snr_db >= 30.0:
        label = "GOOD"
    elif snr_db >= 15.0:
        label = "MODERATE"
    else:
        label = "POOR"

    return label, snr_db
