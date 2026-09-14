"""VoiceGuard Correlation Engine (SQLite Backend).

Monitors flagged high-risk calls and detects coordinated impersonation campaigns
by checking for multi-signal cluster alignment (caller prefix hash, voice score, transaction amount).
"""

from datetime import datetime, timezone
from typing import Any
from storage import log_flagged_call_db, get_all_flagged_calls_db


def log_flagged_call(call_data: dict) -> None:
    """Appends a flagged call entry to the SQLite database if risk_tier is HIGH or CRITICAL."""
    tier = (call_data.get("risk_tier") or "").upper()
    if tier in ["HIGH", "CRITICAL"]:
        entry = {
            "caller_number": str(call_data.get("caller_number") or "").strip(),
            "voice_score": float(call_data.get("score", call_data.get("voice_score", 0.0))),
            "risk_tier": tier,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "transaction_amount": float(call_data.get("transaction_amount") or 0.0),
        }
        log_flagged_call_db(entry)


def check_correlation() -> dict[str, Any]:
    """Scans SQLite flagged call history for coordinated campaign patterns (>=3 calls matching >=2 signals)."""
    calls = get_all_flagged_calls_db()

    if len(calls) < 3:
        return {
            "alert": False,
            "total_flagged_calls": len(calls),
            "message": "Insufficient flagged call history for correlation analysis (minimum 3 required).",
        }

    matched_calls = []
    signals_matched = set()

    # Iterate over all triples of flagged calls
    n = len(calls)
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                c1, c2, c3 = calls[i], calls[j], calls[k]
                alignments = 0
                local_signals = []

                # Signal 1: Caller Prefix Hash Match (first 5 digits hash match)
                p1, p2, p3 = c1.get("prefix_hash"), c2.get("prefix_hash"), c3.get("prefix_hash")
                if p1 and p1 == p2 == p3:
                    alignments += 1
                    local_signals.append("caller_prefix_match")

                # Signal 2: Voice Score Similarity (all within 1.0 of each other)
                s1, s2, s3 = c1["voice_score"], c2["voice_score"], c3["voice_score"]
                if max(s1, s2, s3) - min(s1, s2, s3) <= 1.0:
                    alignments += 1
                    local_signals.append("voice_score_cluster")

                # Signal 3: Transaction Amount Similarity (all within 20% of mean amount)
                a1, a2, a3 = c1["transaction_amount"], c2["transaction_amount"], c3["transaction_amount"]
                if a1 > 0 and a2 > 0 and a3 > 0:
                    mean_a = (a1 + a2 + a3) / 3.0
                    if max(abs(a1 - mean_a), abs(a2 - mean_a), abs(a3 - mean_a)) <= (0.20 * mean_a):
                        alignments += 1
                        local_signals.append("transaction_amount_cluster")

                # Check if 2 or more signals aligned
                if alignments >= 2:
                    for c in [c1, c2, c3]:
                        if c not in matched_calls:
                            matched_calls.append(c)
                    for sig in local_signals:
                        signals_matched.add(sig)

    if len(matched_calls) >= 3 and len(signals_matched) >= 2:
        return {
            "alert": True,
            "matched_calls": matched_calls,
            "signals_matched": sorted(list(signals_matched)),
            "message": "Possible coordinated impersonation campaign detected across multiple flagged calls.",
        }

    return {
        "alert": False,
        "total_flagged_calls": len(calls),
        "message": "No correlation cluster detected.",
    }
