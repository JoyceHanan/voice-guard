"""VoiceGuard Classification Module.

Provides decision boundary classification logic with buffer margin for voice deepfake detection.
"""

def classify(score: float, threshold: float, margin: float = 0.5) -> str:
    """Classifies a score as REAL, FAKE, or INCONCLUSIVE based on a threshold and margin.

    Args:
        score: The model output score (bona-fide logit).
        threshold: The decision boundary score.
        margin: The buffer margin around threshold for inconclusive results.

    Returns:
        "REAL", "FAKE", or "INCONCLUSIVE"
    """
    if score >= threshold + margin:
        return "REAL"
    elif score <= threshold - margin:
        return "FAKE"
    else:
        return "INCONCLUSIVE"


def classify_with_duration_check(
    score: float,
    threshold: float,
    duration_seconds: float,
    min_duration: float = 4.0,
    margin: float = 0.5,
) -> str:
    """Classifies score while checking for minimum required audio duration.

    Args:
        score: Model bona-fide logit output.
        threshold: Decision boundary threshold.
        duration_seconds: Duration of the audio file in seconds.
        min_duration: Minimum required duration in seconds (default: 4.0s).
        margin: Buffer margin around threshold.

    Returns:
        "INCONCLUSIVE (insufficient audio duration)" if duration < min_duration,
        otherwise result of classify(score, threshold, margin).
    """
    if duration_seconds < min_duration:
        return "INCONCLUSIVE (insufficient audio duration)"
    return classify(score, threshold, margin=margin)


def classify_with_quality_and_duration(
    score: float,
    threshold: float,
    duration_seconds: float,
    audio_quality_label: str = "GOOD",
    min_duration: float = 4.0,
    margin: float = 0.5,
    moderate_margin: float = 1.2,
) -> str:
    """Classifies score with dynamic margin widening based on audio quality and duration safety checks.

    - If duration < min_duration -> "INCONCLUSIVE (insufficient audio duration)"
    - If audio_quality_label == "POOR" -> "INCONCLUSIVE (poor audio quality)"
    - If audio_quality_label == "MODERATE" -> Widen margin from 0.5 to 1.2
    - If audio_quality_label == "GOOD" -> Use standard margin (0.5)
    """
    if duration_seconds < min_duration:
        return "INCONCLUSIVE (insufficient audio duration)"

    quality_upper = (audio_quality_label or "").upper()
    if quality_upper == "POOR":
        return "INCONCLUSIVE (poor audio quality)"

    eff_margin = moderate_margin if quality_upper == "MODERATE" else margin
    res = classify(score, threshold, margin=eff_margin)
    if res == "INCONCLUSIVE":
        return f"INCONCLUSIVE (score within buffer margin ±{eff_margin:.1f})"
    return res
