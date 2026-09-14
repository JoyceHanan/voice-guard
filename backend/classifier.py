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
