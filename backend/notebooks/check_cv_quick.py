import sys
from datasets import load_dataset

def check(name, config):
    print(f"Testing {name} config={config}...", flush=True)
    try:
        ds = load_dataset(name, config, split="train", streaming=True)
        item = next(iter(ds))
        print(f"SUCCESS: {name} ({config})", flush=True)
        return True
    except Exception as e:
        print(f"FAILED: {name} ({config}): {e}", flush=True)
        return False

print("=== COMMON VOICE 17.0 ===", flush=True)
check("mozilla-foundation/common_voice_17_0", "hi")
check("mozilla-foundation/common_voice_17_0", "te")

print("\n=== COMMON VOICE 13.0 ===", flush=True)
check("mozilla-foundation/common_voice_13_0", "hi")
check("mozilla-foundation/common_voice_13_0", "te")

print("\n=== COMMON VOICE 11.0 ===", flush=True)
check("mozilla-foundation/common_voice_11_0", "hi")
check("mozilla-foundation/common_voice_11_0", "te")

print("\n=== GOOGLE FLEURS ===", flush=True)
check("google/fleurs", "hi_in")
check("google/fleurs", "te_in")
