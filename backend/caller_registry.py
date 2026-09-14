"""VoiceGuard Caller Registry & Intelligence Module (SQLite Backend).

Queries persistent SQLite storage for known trusted contacts and blocklisted fraud numbers.
"""

from storage import get_known_contact, is_blocklisted, add_to_blocklist_db, add_known_contact


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

    # Check SQLite known_contacts
    known_info = get_known_contact(clean_num)
    if known_info:
        return {
            "category": "known",
            "name": known_info["name"],
            "reason": known_info["reason"],
        }

    # Check SQLite blocklist
    block_info = is_blocklisted(clean_num)
    if block_info:
        return {
            "category": "unknown_flagged",
            "name": None,
            "reason": block_info["reason"],
        }

    return {
        "category": "unknown_neutral",
        "name": None,
        "reason": "Unregistered number",
    }


def add_to_blocklist(phone_number: str, reason: str = "Matches known fraud pattern / blocklist entry") -> bool:
    """Appends a phone number to the fraud blocklist in SQLite."""
    clean_num = (phone_number or "").strip()
    if clean_num:
        add_to_blocklist_db(clean_num, reason=reason)
        return True
    return False
