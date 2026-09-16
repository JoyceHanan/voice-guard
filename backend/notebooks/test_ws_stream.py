"""WebSocket Audio Streaming Client Test Script for VoiceGuard backend.

Simulates live streaming audio by slicing a long audio file into 1.0-second chunks,
sending them over WebSocket (/ws/analyze with 1.0s hop), and receiving real-time updating risk assessments
with side-by-side raw vs. smoothed score outputs.
"""

import asyncio
import io
import json
from pathlib import Path
import sys
import soundfile as sf
import websockets

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AUDIO_FILE = BASE_DIR / "data" / "fake" / "fake_sample.wav"
WS_URL = "ws://127.0.0.1:8000/ws/analyze?api_key=vg_secret_key_12345&claimed_identity=CFO_Rajesh&new_beneficiary=true&urgency=true"


async def run_ws_stream():
    print("=" * 85)
    print("VoiceGuard WebSocket Audio Streaming Test (1.0s Hop, EMA Alpha=0.4 Smoothing)")
    print("=" * 85)
    print(f"Reading input audio file: {AUDIO_FILE.name}")

    audio, sr = sf.read(str(AUDIO_FILE), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    chunk_dur = 1.0  # 1.0-second chunks for 1.0s hop update interval
    samples_per_chunk = int(chunk_dur * sr)
    total_samples = len(audio)

    chunks = []
    for i in range(0, total_samples, samples_per_chunk):
        c_audio = audio[i : i + samples_per_chunk]
        if len(c_audio) < samples_per_chunk:
            continue
        buf = io.BytesIO()
        sf.write(buf, c_audio, sr, format="WAV", subtype="PCM_16")
        chunks.append(buf.getvalue())

    print(f"Split audio into {len(chunks)} continuous 1.0-second chunks.")
    print(f"Connecting to WebSocket: {WS_URL}...\n")
    print(f"{'Chunk':<8} {'Status':<12} {'Raw Score':>10} {'Smoothed Score':>16} {'Result':<10} {'Risk Tier':<12}")
    print("-" * 85)

    async with websockets.connect(WS_URL) as ws:
        for idx, chunk in enumerate(chunks, 1):
            await ws.send(chunk)

            response = await ws.recv()
            data = json.loads(response)

            status = data.get("status")
            if status == "buffering":
                dur = data.get("duration_accumulated")
                print(f"Chunk {idx:<2}   BUFFERING    {'N/A':>10} {'N/A':>16} {'N/A':<10} {f'Accumulating {dur}s/4.0s':<12}")
            else:
                raw_s = data.get("raw_score")
                smooth_s = data.get("smoothed_score")
                res = data.get("voice_result")
                tier = data.get("risk_tier")
                print(f"Chunk {idx:<2}   EVALUATED    {raw_s:>10.2f} {smooth_s:>16.2f} {res:<10} {tier:<12}")

            await asyncio.sleep(0.3)

        print("-" * 85)
        print("Streaming test completed successfully.")


if __name__ == "__main__":
    asyncio.run(run_ws_stream())
