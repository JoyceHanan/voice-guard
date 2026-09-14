"""VoiceGuard Caller Registry & Intelligence Module.

Maintains in-memory directory of known trusted contacts and blocklisted fraud numbers.
Categorizes caller phone numbers into:
- "known": Registered trusted contact
- "unknown_flagged": Matches known fraud/blocklist entry
- "unknown_neutral": Unregistered number with no negative intelligence
"""

# Seeded known contacts dictionary: { phone_number: name }
KNOWN_CONTACTS = {
    "+911234567890": "Rajesh Kumar (CFO)",
    "+15550192834": "Alice Smith (Treasurer)",
    "+442079460912": "David Miller (Director)",
}

# Seeded fraud blocklist set/list
BLOCKLIST = [
    "+19998887777",
    "+919999999999",
]


def classify_caller(phone_number: str) -> dict:
    """Classifies a caller's phone number into known, unknown_flagged, or unknown_neutral.

    Args:
        phone_number: Phone number string (e.g. "+911234567890")

    Returns:
        dict: {"category": str, "name": Optional[str], "reason": Optional[str]}
    """
    clean_num = (phone_number or "").strip()

    if not clean_num:
        return {"category": "unknown_neutral", "name": None, "reason": "No caller number provided"}

    if clean_num in KNOWN_CONTACTS:
        return {
            "category": "known",
            "name": KNOWN_CONTACTS[clean_num],
            "reason": "Registered trusted contact",
        }

    if clean_num in BLOCKLIST:
        return {
            "category": "unknown_flagged",
            "name": None,
            "reason": "Matches known fraud pattern / blocklist entry",
        }

    return {
        "category": "unknown_neutral",
        "name": None,
        "reason": "Unregistered number",
    }


def add_to_blocklist(phone_number: str) -> bool:
    """Appends a phone number to the fraud blocklist."""
    clean_num = (phone_number or "").strip()
    if clean_num and clean_num not in BLOCKLIST:
        BLOCKLIST.append(clean_num)
        return True
    return False
