"""VoiceGuard Multi-Factor Risk Fusion Engine.

Combines AI anti-spoofing score (AASIST-L), speaker verification similarity (ECAPA-TDNN),
audio quality SNR metrics, caller intelligence classification, and transaction metadata
into a unified risk assessment.
"""

import math
from typing import Any, Optional

RECOMMENDED_THRESHOLD = 2.10


def compute_risk(
    voice_score: float,
    speaker_similarity: Optional[float],
    audio_quality_label: str,
    duration_seconds: float,
    known_caller: bool = False,
    caller_category: Optional[str] = None,
    new_beneficiary: bool = False,
    urgency: bool = False,
    min_duration: float = 4.0,
) -> dict[str, Any]:
    """Computes composite risk tier, numeric score (0-100), and factor breakdown.

    Args:
        voice_score: AASIST-L logit score.
        speaker_similarity: ECAPA-TDNN cosine similarity (or None).
        audio_quality_label: "GOOD", "MODERATE", or "POOR".
        duration_seconds: Audio length in seconds.
        known_caller: Legacy boolean fallback if caller_category is omitted.
        caller_category: "known", "unknown_neutral", or "unknown_flagged".
        new_beneficiary: Boolean flag for new transfer recipient.
        urgency: Boolean flag for high-urgency claim/request.
        min_duration: Minimum required duration (default: 4.0s).

    Returns:
        {
            "tier": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "INCONCLUSIVE",
            "score": float | None,
            "reason": str | None,
            "breakdown": dict
        }
    """
    # 1. Inconclusive Safety Checks
    if duration_seconds < min_duration:
        return {
            "tier": "INCONCLUSIVE",
            "score": None,
            "reason": f"Insufficient audio duration ({duration_seconds:.2f}s < minimum {min_duration:.1f}s).",
            "breakdown": {},
        }

    if audio_quality_label.upper() == "POOR":
        return {
            "tier": "INCONCLUSIVE",
            "score": None,
            "reason": "Poor audio quality / severe background noise (SNR < 15 dB).",
            "breakdown": {},
        }

    breakdown = {}

    # 2. Voice Spoof Risk Component (from AASIST-L logit)
    # Using logistic sigmoid relative to threshold=2.10: score lower than 2.10 indicates fake.
    logit_distance = RECOMMENDED_THRESHOLD - voice_score
    voice_risk_norm = 100.0 / (1.0 + math.exp(-logit_distance / 2.0))
    voice_risk_norm = max(0.0, min(100.0, voice_risk_norm))

    has_speaker = speaker_similarity is not None

    if has_speaker:
        w_voice = 0.40
        w_speaker = 0.30
        w_context = 0.30
    else:
        w_voice = 0.50
        w_speaker = 0.00
        w_context = 0.50

    voice_contrib = voice_risk_norm * w_voice
    breakdown["voice_spoof_risk"] = {
        "raw_score": round(float(voice_score), 2),
        "normalized_risk_score": round(float(voice_risk_norm), 2),
        "weight": w_voice,
        "weighted_contribution": round(float(voice_contrib), 2),
    }

    # 3. Speaker Mismatch Risk Component
    if has_speaker:
        speaker_risk_norm = (1.0 - max(0.0, min(1.0, float(speaker_similarity)))) * 100.0
        speaker_contrib = speaker_risk_norm * w_speaker
        breakdown["speaker_mismatch_risk"] = {
            "raw_similarity": round(float(speaker_similarity), 4),
            "normalized_risk_score": round(float(speaker_risk_norm), 2),
            "weight": w_speaker,
            "weighted_contribution": round(float(speaker_contrib), 2),
        }
    else:
        breakdown["speaker_mismatch_risk"] = {
            "status": "skipped (no claimed_identity provided)",
            "weighted_contribution": 0.0,
        }

    # 4. Contextual Transaction Metadata & Caller Intelligence Risk Component
    # Caller Risk:
    # - "known" -> 0 risk
    # - "unknown_neutral" -> +35 risk
    # - "unknown_flagged" -> +55 risk (+20 extra penalty for fraud blocklist match)
    cat_lower = (caller_category or "").lower()
    if cat_lower == "known":
        caller_risk_pts = 0.0
        eff_category = "known"
    elif cat_lower == "unknown_flagged":
        caller_risk_pts = 55.0
        eff_category = "unknown_flagged"
    elif cat_lower == "unknown_neutral":
        caller_risk_pts = 35.0
        eff_category = "unknown_neutral"
    else:
        # Fallback to known_caller boolean
        if known_caller:
            caller_risk_pts = 0.0
            eff_category = "known"
        else:
            caller_risk_pts = 35.0
            eff_category = "unknown_neutral"

    context_risk_norm = caller_risk_pts
    if new_beneficiary:
        context_risk_norm += 35.0
    if urgency:
        context_risk_norm += 30.0

    context_contrib = context_risk_norm * w_context
    breakdown["transaction_context_risk"] = {
        "caller_category": eff_category,
        "new_beneficiary": new_beneficiary,
        "urgency": urgency,
        "normalized_risk_score": round(float(context_risk_norm), 2),
        "weight": w_context,
        "weighted_contribution": round(float(context_contrib), 2),
    }

    # 5. Composite Risk Score & Risk Tier Assignment
    if has_speaker:
        total_risk_score = voice_contrib + speaker_contrib + context_contrib
    else:
        total_risk_score = voice_contrib + context_contrib

    total_risk_score = round(max(0.0, min(100.0, total_risk_score)), 2)

    if total_risk_score < 30.0:
        tier = "LOW"
    elif total_risk_score < 60.0:
        tier = "MEDIUM"
    elif total_risk_score < 85.0:
        tier = "HIGH"
    else:
        tier = "CRITICAL"

    return {
        "tier": tier,
        "score": total_risk_score,
        "reason": None,
        "breakdown": breakdown,
    }
