import sys
from datasets import load_dataset

def check(name, config=None):
    print(f"Testing name='{name}' config='{config}'...", flush=True)
    try:
        if config:
            ds = load_dataset(name, config, split="train", streaming=True)
        else:
            ds = load_dataset(name, split="train", streaming=True)
        item = next(iter(ds))
        print(f"SUCCESS: {name} ({config}) -> keys: {list(item.keys())}", flush=True)
        return True
    except Exception as e:
        print(f"FAILED: {name} ({config}): {e}", flush=True)
        return False

print("=== LEGACY COMMON VOICE ===", flush=True)
check("legacy-datasets/common_voice", "hi")
check("legacy-datasets/common_voice", "te")
check("legacy-datasets/common_voice", "ta")

print("\n=== OTHER SPECIFIC DATASETS ===", flush=True)
check("bnriiitb/telugu_asr")
check("parambharat/telugu_asr_corpus")
