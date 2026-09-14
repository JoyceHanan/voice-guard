"""VoiceGuard SQLite Storage, Encryption, and Anonymization Module.

Provides persistent SQLite database storage for:
1. enrolled_speakers (encrypted speaker embeddings)
2. known_contacts (SHA-256 hashed phone numbers)
3. blocklist (SHA-256 hashed phone numbers)
4. flagged_calls (SHA-256 hashed phone numbers & campaign logs)
"""

import datetime
import hashlib
import io
import os
from pathlib import Path
import sqlite3

from cryptography.fernet import Fernet
import numpy as np
import torch

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "voiceguard.db"

KEY_FILE = BASE_DIR / ".encryption_key"


def get_encryption_fernet() -> Fernet:
    """Loads or generates Fernet symmetric key stored in backend/.encryption_key."""
    if not KEY_FILE.exists():
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
    else:
        key = KEY_FILE.read_bytes()
    return Fernet(key)


FERNET = get_encryption_fernet()


def hash_phone(phone_number: str) -> str:
    """Hashes phone number string using SHA-256."""
    clean = (phone_number or "").strip()
    if not clean:
        return ""
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def encrypt_tensor(tensor: torch.Tensor) -> bytes:
    """Converts PyTorch tensor to numpy bytes and encrypts with Fernet."""
    arr = tensor.detach().cpu().numpy().astype(np.float32)
    raw_bytes = arr.tobytes()
    return FERNET.encrypt(raw_bytes)


def decrypt_tensor(encrypted_bytes: bytes) -> torch.Tensor:
    """Decrypts Fernet bytes and reconstructs 1D PyTorch float32 tensor."""
    raw_bytes = FERNET.decrypt(encrypted_bytes)
    arr = np.frombuffer(raw_bytes, dtype=np.float32)
    return torch.from_numpy(arr.copy())


def get_db_connection() -> sqlite3.Connection:
    """Returns sqlite3 Connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes SQLite database schema and seeds default known contacts & blocklist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrolled_speakers (
        speaker_id TEXT PRIMARY KEY,
        embedding BLOB NOT NULL,
        enrolled_at TIMESTAMP NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS known_contacts (
        phone_number TEXT PRIMARY KEY,
        name TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blocklist (
        phone_number TEXT PRIMARY KEY,
        reason TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flagged_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caller_number TEXT NOT NULL,
        prefix_hash TEXT NOT NULL,
        voice_score REAL NOT NULL,
        risk_tier TEXT NOT NULL,
        transaction_amount REAL NOT NULL,
        timestamp TIMESTAMP NOT NULL
    )
    """)

    conn.commit()

    # Seed known_contacts if empty
    cursor.execute("SELECT COUNT(*) FROM known_contacts")
    if cursor.fetchone()[0] == 0:
        default_known = [
            ("+911234567890", "Rajesh Kumar (CFO)"),
            ("+15550192834", "Alice Smith (Treasurer)"),
            ("+442079460912", "David Miller (Director)"),
        ]
        for phone, name in default_known:
            cursor.execute(
                "INSERT OR IGNORE INTO known_contacts (phone_number, name) VALUES (?, ?)",
                (hash_phone(phone), name),
            )

    # Seed blocklist if empty
    cursor.execute("SELECT COUNT(*) FROM blocklist")
    if cursor.fetchone()[0] == 0:
        default_blocklist = [
            ("+19998887777", "Known fraud blocklist entry"),
            ("+919999999999", "Known fraud blocklist entry"),
        ]
        for phone, reason in default_blocklist:
            cursor.execute(
                "INSERT OR IGNORE INTO blocklist (phone_number, reason) VALUES (?, ?)",
                (hash_phone(phone), reason),
            )

    conn.commit()
    conn.close()


# Run init on module load
init_db()


# --- Database Operations API ---

def save_enrolled_speaker(speaker_id: str, embedding: torch.Tensor):
    """Encrypts and persists speaker embedding in SQLite."""
    clean_id = speaker_id.strip()
    enc_blob = encrypt_tensor(embedding)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db_connection()
    conn.execute(
        "INSERT OR REPLACE INTO enrolled_speakers (speaker_id, embedding, enrolled_at) VALUES (?, ?, ?)",
        (clean_id, enc_blob, now),
    )
    conn.commit()
    conn.close()


def load_enrolled_speakers() -> dict[str, torch.Tensor]:
    """Reads all enrolled speakers from SQLite and decrypts embeddings."""
    conn = get_db_connection()
    rows = conn.execute("SELECT speaker_id, embedding FROM enrolled_speakers").fetchall()
    conn.close()
    result = {}
    for row in rows:
        result[row["speaker_id"]] = decrypt_tensor(row["embedding"])
    return result


def get_enrolled_speaker_ids() -> list[str]:
    """Returns list of enrolled speaker IDs."""
    conn = get_db_connection()
    rows = conn.execute("SELECT speaker_id FROM enrolled_speakers").fetchall()
    conn.close()
    return [row["speaker_id"] for row in rows]


def get_known_contact(phone_number: str) -> dict | None:
    """Queries known_contacts using hashed phone number."""
    hashed = hash_phone(phone_number)
    conn = get_db_connection()
    row = conn.execute("SELECT name FROM known_contacts WHERE phone_number = ?", (hashed,)).fetchone()
    conn.close()
    if row:
        return {"name": row["name"], "reason": "Registered trusted contact"}
    return None


def is_blocklisted(phone_number: str) -> dict | None:
    """Queries blocklist using hashed phone number."""
    hashed = hash_phone(phone_number)
    conn = get_db_connection()
    row = conn.execute("SELECT reason FROM blocklist WHERE phone_number = ?", (hashed,)).fetchone()
    conn.close()
    if row:
        return {"reason": row["reason"]}
    return None


def add_known_contact(phone_number: str, name: str):
    """Adds known contact with hashed phone number."""
    hashed = hash_phone(phone_number)
    conn = get_db_connection()
    conn.execute(
        "INSERT OR REPLACE INTO known_contacts (phone_number, name) VALUES (?, ?)",
        (hashed, name),
    )
    conn.commit()
    conn.close()


def add_to_blocklist_db(phone_number: str, reason: str = "Fraud pattern"):
    """Adds phone number to blocklist with hash."""
    hashed = hash_phone(phone_number)
    conn = get_db_connection()
    conn.execute(
        "INSERT OR REPLACE INTO blocklist (phone_number, reason) VALUES (?, ?)",
        (hashed, reason),
    )
    conn.commit()
    conn.close()


def log_flagged_call_db(call_data: dict):
    """Logs flagged call into SQLite table flagged_calls with hashed phone and prefix hash."""
    caller_num = str(call_data.get("caller_number", "")).strip()
    hashed_num = hash_phone(caller_num)
    # First 5 characters for prefix cluster matching
    prefix = caller_num[:5] if len(caller_num) >= 5 else caller_num
    hashed_prefix = hash_phone(prefix)

    score = float(call_data.get("voice_score", call_data.get("score", 0.0)))
    tier = str(call_data.get("risk_tier", ""))
    amount = float(call_data.get("transaction_amount", 0.0))
    ts = str(call_data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat()))

    conn = get_db_connection()
    conn.execute(
        """INSERT INTO flagged_calls 
        (caller_number, prefix_hash, voice_score, risk_tier, transaction_amount, timestamp) 
        VALUES (?, ?, ?, ?, ?, ?)""",
        (hashed_num, hashed_prefix, score, tier, amount, ts),
    )
    conn.commit()
    conn.close()


def get_all_flagged_calls_db() -> list[dict]:
    """Retrieves all logged flagged calls from SQLite."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, caller_number, prefix_hash, voice_score, risk_tier, transaction_amount, timestamp FROM flagged_calls"
    ).fetchall()
    conn.close()
    calls = []
    for r in rows:
        calls.append({
            "id": r["id"],
            "caller_number": r["caller_number"],
            "prefix_hash": r["prefix_hash"],
            "voice_score": r["voice_score"],
            "risk_tier": r["risk_tier"],
            "transaction_amount": r["transaction_amount"],
            "timestamp": r["timestamp"],
        })
    return calls
