"""VoiceGuard Policy Engine.

Maps risk assessment tiers ("LOW", "MEDIUM", "HIGH", "CRITICAL", "INCONCLUSIVE")
to actionable security response policies and user-facing messages.
"""

def get_recommended_action(risk_tier: str) -> dict:
    """Returns recommended security policy action and explanation message based on risk tier.

    Args:
        risk_tier: "LOW", "MEDIUM", "HIGH", "CRITICAL", or "INCONCLUSIVE"

    Returns:
        dict: {"tier": str, "action": str, "message": str}
    """
    tier_upper = (risk_tier or "").upper()

    if tier_upper == "LOW":
        return {
            "tier": "LOW",
            "action": "ALLOW",
            "message": "No action needed. Call may proceed normally.",
        }
    elif tier_upper == "MEDIUM":
        return {
            "tier": "MEDIUM",
            "action": "MONITOR",
            "message": "Continue monitoring. No interruption required, but flagged for review.",
        }
    elif tier_upper == "HIGH":
        return {
            "tier": "HIGH",
            "action": "VERIFY",
            "message": (
                "Recommend independent verification before proceeding "
                "(callback on a known number, MFA, or security question)."
            ),
        }
    elif tier_upper == "CRITICAL":
        return {
            "tier": "CRITICAL",
            "action": "ESCALATE",
            "message": (
                "Do not authorize any sensitive action. Escalate to supervisor "
                "and require independent callback before proceeding."
            ),
        }
    else:  # INCONCLUSIVE or unknown
        return {
            "tier": "INCONCLUSIVE",
            "action": "VERIFY",
            "message": (
                "Unable to confidently assess this call. Recommend independent "
                "verification as a precaution — this is not an accusation, just insufficient signal."
            ),
        }
