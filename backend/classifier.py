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
