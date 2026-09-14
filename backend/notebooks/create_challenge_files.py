"""Script to generate deliberate wrong and correct challenge test audio WAV files using gTTS."""

import io
from pathlib import Path
import soundfile as sf
import librosa
from gtts import gTTS

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "challenge_test"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def generate_wav(text: str, filename: str):
    tts = gTTS(text=text, lang="en", slow=False)
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    y, sr = librosa.load(mp3_fp, sr=16000, mono=True)
    out_path = DATA_DIR / filename
    sf.write(out_path, y, 16000, subtype="PCM_16")
    print(f"Generated {out_path.name}: phrase='{text}'")


if __name__ == "__main__":
    generate_wav("bright solar signal", "deliberate_wrong_answer.wav")
    generate_wav("bright solar system", "deliberate_correct_answer.wav")
