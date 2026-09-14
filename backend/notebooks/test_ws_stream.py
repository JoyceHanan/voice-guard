"""WebSocket Audio Streaming Client Test Script for VoiceGuard backend.

Simulates live streaming audio by slicing a long audio file into 2-second chunks,
sending them over WebSocket (/ws/analyze), and receiving real-time updating risk assessments.
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
    print("=" * 80)
    print("VoiceGuard WebSocket Audio Streaming Test")
    print("=" * 80)
    print(f"Reading input audio file: {AUDIO_FILE.name}")

    audio, sr = sf.read(str(AUDIO_FILE), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    chunk_dur = 2.0  # 2-second chunks
    samples_per_chunk = int(chunk_dur * sr)
    total_samples = len(audio)

    chunks = []
    for i in range(0, total_samples, samples_per_chunk):
        c_audio = audio[i : i + samples_per_chunk]
        if len(c_audio) < samples_per_chunk:
            continue
        # Convert to WAV bytes
        buf = io.BytesIO()
        sf.write(buf, c_audio, sr, format="WAV", subtype="PCM_16")
        chunks.append(buf.getvalue())

    print(f"Split audio into {len(chunks)} continuous 2.0-second chunks.")
    print(f"Connecting to WebSocket: {WS_URL}...\n")

    async with websockets.connect(WS_URL) as ws:
        for idx, chunk in enumerate(chunks, 1):
            print(f"--> Sending Chunk {idx} ({chunk_dur}s)...")
            await ws.send(chunk)

            # Receive response over WebSocket
            response = await ws.recv()
            data = json.loads(response)

            status = data.get("status")
            if status == "buffering":
                print(f"    [BUFFERING]: {data.get('message')}")
            else:
                score = data.get("score")
                res = data.get("voice_result")
                tier = data.get("risk_tier")
                sim = data.get("speaker_similarity")
                action = data.get("recommended_action", {}).get("action")
                print(f"    [EVALUATED 4.0s Window]: Score={score}, Result='{res}', Similarity={sim}, RiskTier='{tier}', Action='{action}'")

            await asyncio.sleep(0.5)  # Simulate real-time streaming arrival

        print("\nStreaming test finished cleanly.")


if __name__ == "__main__":
    asyncio.run(run_ws_stream())
